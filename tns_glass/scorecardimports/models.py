from django.db import models
from smartmin.models import *
from seasons.models import Season
from standards.models import *
from wetmills.models import *
from scorecards.models import *
from tasks import import_scorecards
import datetime
import csv
import re
from django.utils.translation import ugettext_lazy as _

class ScorecardImport(SmartModel):
    season = models.ForeignKey(Season, verbose_name=_("Season"),
                               help_text=_("The season scorecards are being imported for"))
    csv_file = models.FileField(upload_to="scorecard_imports", 
                                verbose_name=_("Import CSV File"),
                                help_text=_("The CSV file to import for this season, must be formatted according to the season template"))
    import_log = models.TextField(verbose_name=_("Import Log"), help_text=_("Any logging information about this import"))
    task_id = models.CharField(null=True, max_length=64, verbose_name=_("Task Id"))

    def __unicode__(self):
        return "CSV Import for %s %s" % (self.season.country.name, self.season.name)

    def start(self): # pragma: no cover
        result = import_scorecards.delay(self)
        self.task_id = result.task_id
        self.import_log = "Queuing file for import.\n"
        self.save()

    def get_status(self):
        status = 'PENDING'
        if self.task_id: # pragma: no cover
            result = import_scorecards.AsyncResult(self.task_id)
            status = result.state

        return status

    def log(self, message):
        self.import_log += "%s\n" % message
        self.modified_on = datetime.datetime.now()
        self.save()

    class Meta:
        ordering = ('-modified_on',)

def lookup_standard(season, name):
    match = re.match("^(.*?) - (.*)$", name, re.DOTALL | re.MULTILINE)
    if match:
        category_slug = match.group(1).strip()
        
        try:
            category = StandardCategory.objects.get(acronym__iexact=category_slug)
        except StandardCategory.DoesNotExist:
            raise Exception("Unable to find standards category with an acronym of '%s'" % category_slug)

        standard_name = match.group(2).strip()

        # look up the standard
        try:
            standard = Standard.objects.get(name__iexact=standard_name, category=category)
        except Standard.DoesNotExist:
            raise Exception("Unable to find standard in category '%s' with name '%s'" % (category.name, standard_name))

        # make sure it is configured for our season
        if not season.standards.filter(pk=standard.pk):
            raise Exception("Standard '%s' is not configured for this season" % (standard.name))

        return standard
    else:
        raise Exception("Invalid format for standard header '%s', incorrect format, should be like: 'SRE - No Child Labour'" %
                        name)

def lookup_wetmill(season, name):
    name = name.strip()

    if name == '':
        return None

    try:
        wetmill = Wetmill.objects.get(country=season.country, name__exact=name, is_active=True)
    except Wetmill.DoesNotExist:
        raise Exception("Unable to find wetmill in %s with name '%s'" % (season.country.name, name))
    
    return wetmill

def parse_standard_value(standard, value):
    value = value.lower().strip()

    if value == '':
        raise Exception("Missing value for standard: %s" % standard.name)

    # minimum requirements must be either 'PASS' or 'FAIL'
    if standard.kind == 'MR':
        if value == 'pass':
            return 100
        elif value == 'fail':
            return 0
        else:
            raise Exception("Invalid value '%s' for '%s' minimum requirement, must be either PASS or FAIL" % 
                            (value, standard.name))

    # best practices must be between 0% and 100%
    else:
        try:
            percentage = int(value.replace('%', '').strip())
        except:
            raise Exception("Invalid value '%s' for '%s' best practice, must be a percentage between 0%% and 100%%" % 
                            (value, standard.name))

        if percentage < 0 or percentage > 100:
            raise Exception("Invalid value '%s' for '%s' best practice, must be a percentage between 0%% and 100%%" % 
                            (value, standard.name))

        return percentage

def get_closure(season, name):
    name = name.strip().lower()

    if not name:
        return None

    if name == 'wet mill':
        def set_wetmill(season, context, value):
            context['wetmill'] = lookup_wetmill(season, value)
        return set_wetmill

    elif name.lower() == 'client id':
        def set_client_id(season, context, value):
            if value.strip():
                context['client_id'] = value.strip()
            else:
                context['client_id'] = None
        return set_client_id

    elif name.lower() == 'audit date':
        def set_audit_date(season, context, value):
            try:
                context['audit_date'] = datetime.datetime.strptime(value, "%d-%b-%y").date()
            except:
                raise Exception("Invalid format for audit date '%s' must be like: '28-JUN-11'" % value)
        return set_audit_date

    elif name.lower() == 'auditor':
        def set_auditor(season, context, value):
            context['auditor'] = value.strip()
        return set_auditor

    else:
        standard = lookup_standard(season, name)
        def build_set_standard(standard):
            def set_standard(season, context, value):
                context['entries'][standard] = parse_standard_value(standard, value)
            return set_standard
                
        return build_set_standard(standard)

def import_season_scorecards(season, csv_file, user, logger):
    from django.db import transaction
    transaction.commit()    

    scorecards = []

    rows = []
    reader = csv.reader(open(csv_file, 'rU'))
    for row in reader:
        rows.append(row)

    try:
        # build our closures
        closures = []
        for col in rows[0]:
            closures.append(get_closure(season, col))

        # add each row
        for row in rows[1:]:
            context = dict(entries=dict())
            for (index, value) in enumerate(row):
                closure = closures[index]

                if closure:
                    closure(season, context, value)

                # shortcut if there's no wetmill
                if not context['wetmill']:
                    break

            # only create a scorecard if there is a wetmill name
            if context['wetmill']:
                logger.write("Processing %s scorecard.\n" % context['wetmill'])

                # delete any previous scorecard
                Scorecard.objects.filter(season=season, wetmill=context['wetmill']).delete()
                scorecard = Scorecard.objects.create(season=season, wetmill=context['wetmill'], auditor=context['auditor'],
                                                     client_id=context['client_id'], audit_date=context['audit_date'],
                                                     created_by=user, modified_by=user)

                # add each entry
                entries = context['entries']
                for standard in entries.keys():
                    value = entries[standard]
                    scorecard.add_entry(standard, value, user)

                # try to finalize the scorecard
                scorecard.finalize()
                scorecard.save()
                scorecards.append(scorecard)

    except Exception as e:
        import sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()

        if logger:
            logger.write("\nError Details:\n\n")
            logger.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # if an errors occurs, roll back any part of our import
        transaction.rollback()
        raise e

    return scorecards

def rows_to_csv(rows):
    try:
        from cStringIO import StringIO
    except ImportError: # pragma: no cover
        from StringIO import StringIO

    output_buffer = StringIO()
    writer = csv.writer(output_buffer)
    for row in rows:
        writer.writerow(row)
    
    return output_buffer.getvalue()

def build_sample_rows(season):
    """
    Returns a 2D array of strings that represents a sample CSV for import of a Season's scorecard
    entries
    """
    rows = []
    top_row = ["Wet Mill", "Client Id", "Auditor", "Audit Date", ]

    for standard in season.get_standards():
        top_row.append("%s - %s" % (standard.category.acronym, standard.name))

    rows.append(top_row)

    # now a sample row
    sample_row = ["Nasho", "", "John Doe", "21-Jun-11"]

    mr_values = ["PASS", "FAIL"]
    bp_values = ["100%", "75%", "50%", "0%"] 

    for (index, standard) in enumerate(season.get_standards()):
        if standard.kind == 'MR':
            sample_row.append(mr_values[index % len(mr_values)])
        else:
            sample_row.append(bp_values[index % len(bp_values)])

    rows.append(sample_row)
    return rows
