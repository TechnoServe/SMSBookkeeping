from django.db import models
from locales.models import *
from smartmin.models import SmartModel
from seasons.models import Season
from csps.models import CSP
from datetime import datetime
import csv
from .tasks import import_wetmills
from django.utils.translation import ugettext_lazy as _

class Wetmill(SmartModel):
    country = models.ForeignKey(Country, verbose_name=_("Country"),
                                help_text=_("What country this wetmill is located in"))

    name = models.CharField(max_length=64, verbose_name=_("Name"),
                            help_text=_("The name of this wetmill, in English"))

    sms_name = models.SlugField(max_length=64, unique=True, verbose_name=_("SMS Name"),
                                help_text=_("The short name used when referring to this wetmill via SMS. Must be unique and cannot contains spaces."))

    description = models.TextField(null=True, blank=True, verbose_name=_("Description"),
                                   help_text=_("A short description of this wetmill. This will be displayed on the public page."))

    province =  models.ForeignKey(Province, verbose_name=_("Province"),
                                  help_text=_("What province this wetmill is located in"))

    year_started = models.IntegerField(max_length=4, null=True, blank=True, verbose_name=_("Year Started"),
                                       help_text=_("When this wetmill was started"))

    latitude = models.DecimalField(max_digits=20, decimal_places=16, null=True, blank=True, verbose_name=_("Latitude"))

    longitude = models.DecimalField(max_digits=20, decimal_places=16, null=True, blank=True, verbose_name=_("Longitude"))

    altitude = models.IntegerField(max_length=5, null=True, blank=True, verbose_name=_("Altitude"),
                                   help_text=_("The altitude of this wetmill, in meters."))

    def get_most_recent_transparency_report(self):
        """
        Returns the most recent transparency report for a finalized season, or None if there is none
        """
        reports = self.reports.filter(is_finalized=True, season__is_finalized=True).order_by('-season__name')
        if reports:
            return reports[0]
        else :
            return None

    def get_most_recent_scorecard(self):
        """
        Returns the most recent scorecard for a finalized season, or None if there is none
        """
        scorecards = self.scorecards.filter(is_finalized=True, season__is_finalized=True).order_by('-season__name')
        if scorecards:
            scorecard = scorecards[0]
            scorecard.metrics = scorecard.calculate_metrics()
            return scorecard
        else :
            return None

    def current_csp(self):
        last_season = Season.objects.filter(country=self.country)
        if last_season:
            wetmill_csp = WetmillCSPSeason.objects.filter(wetmill=self, season=last_season[0])
            if wetmill_csp:
                return wetmill_csp[0].csp

        return None

    def get_csp_for_season(self, season):
        matches = WetmillCSPSeason.objects.filter(season=season, wetmill=self)
        if matches:
            return matches[0].csp
        else:
            return None

    def set_csp_for_season(self, season, csp):
        # clear out the current mapping for this season
        WetmillCSPSeason.objects.filter(wetmill=self, season=season).delete()

        # if there is a new csp mapping, set it
        if not csp is None:
            return WetmillCSPSeason.objects.create(wetmill=self, season=season, csp=csp)

    def get_accounting_for_season(self, season):
        matches = WetmillSeasonAccountingSystem.objects.filter(season=season, wetmill=self)
        if matches:
            return matches[0].accounting_system
        else:
            return ACC_NONE

    def get_accounting_system(self):
        """
        Returns the most recent accounting system for this wetmill
        """
        systems = self.get_accounting_systems()
        if systems:
            return systems[0].accounting_system
        else:
            ACC_NONE

    def get_accounting_system_display(self, accounting_system):
        for system in ACCOUNTING_SYSTEM_CHOICES:
            if system[0] == accounting_system:
                return system[1]

        return "None"

    def set_accounting_system(self, accounting_system):
        # get the last season
        seasons = Season.objects.filter(country=self.country)
        if seasons:
            self.set_accounting_for_season(seasons[0], accounting_system)

    def set_accounting_for_season(self, season, accounting_system):
        # clear out the current system for this season
        WetmillSeasonAccountingSystem.objects.filter(wetmill=self, season=season).delete()

        # if there is a new csp mapping, set it
        return WetmillSeasonAccountingSystem.objects.create(wetmill=self,
                                                            season=season,
                                                            accounting_system=accounting_system)

    def get_accounting_systems(self):
        return WetmillSeasonAccountingSystem.objects.filter(wetmill=self)

    def get_season_csps(self):
        return WetmillCSPSeason.objects.filter(wetmill=self)

    def get_photo_count(self):
        if len(self.photos.filter(is_main=True, is_active=True)) == 0:
            return len(self.photos.filter(is_main=False, is_active=True)[1:])
        else:
            return len(self.photos.filter(is_main=False, is_active=True))

    def get_non_main_photos(self):
        if len(self.photos.filter(is_main=True, is_active=True)) == 0:
            return self.photos.filter(is_main=False, is_active=True)[1:]
        else:
            return self.photos.filter(is_main=False, is_active=True)

    def get_main_photo(self):
        main_photos = self.photos.filter(is_main=True, is_active=True)
        if len(main_photos) > 0:
            return main_photos[0]
        elif len(self.photos.all()) > 0:
            return self.photos.all()[0]
        else:
            return None

    def __unicode__(self):
        return self.name

    # make the most recent report an easy property
    report = property(get_most_recent_transparency_report)

    # make the most recent scorecard an easy property
    scorecard = property(get_most_recent_scorecard)

    class Meta:
        unique_together = ('country', 'name')
        ordering = ('name',)

class WetmillCSPSeason(models.Model):
    wetmill = models.ForeignKey(Wetmill)
    csp = models.ForeignKey(CSP)
    season = models.ForeignKey(Season)

    def __unicode__(self):
        return "%s - %s = %s" % (self.season, self.csp.name, self.wetmill.name)

    class Meta:
        unique_together = ('wetmill', 'season')
        ordering = ('-season__name', 'csp__name', 'wetmill__name')

ACC_NONE = 'NONE'
ACC_FULL = 'FULL'
ACC_LITE = 'LITE'
ACC_2012 = '2012'
ACC_LIT2 = 'LIT2'
ACC_GTWB = 'GTWB'

ACCOUNTING_SYSTEM_CHOICES = ((ACC_NONE, _("No Data Collection")),
                             (ACC_FULL, _("2011 SMS System (legacy)")),
                             (ACC_LITE, _("2011 Light System (legacy)")),
                             (ACC_2012, _("Full SMS Data Collection (current)")),
                             (ACC_LIT2, _("Light SMS Data Collection (current)")),
                             (ACC_GTWB, _("Guatemala Web Accouting (current)")))

class WetmillSeasonAccountingSystem(models.Model):
    """
    The accounting system used by a wetmill for a particular season
    """
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"),
                                help_text=_("The wetmill the accounting system is for"))
    season = models.ForeignKey(Season, verbose_name=_("Season"),
                               help_text=_("The season we are talking about"))
    accounting_system = models.CharField(max_length=32, choices=ACCOUNTING_SYSTEM_CHOICES, verbose_name=_("Accounting System"),
                                         help_text=_("What accounting system should be used for this wetmill for this season"))

    class Meta:
        unique_together = ('wetmill', 'season')
        ordering = ('-season__name', 'wetmill__name', 'accounting_system')


class WetmillImport(SmartModel):
    country = models.ForeignKey(Country, verbose_name=_("Country"),
                                help_text=_("The country the wetmills will be imported to"))
    csv_file = models.FileField(upload_to="wetmill_imports",
                                verbose_name=_("Import CSV File"),
                                help_text=_("The CSV file to import, must be formatted according to the wetmill import template"))
    import_log = models.TextField(verbose_name=_("Import Log"), help_text=_("Any logging information about this import"))
    task_id = models.CharField(null=True, max_length=64, verbose_name=_("Task ID"))

    def __unicode__(self):
        return "Wetmill Import for %s" % self.country.name

    def start(self): # pragma: no cover
        result = import_wetmills.delay(self)
        self.task_id = result.task_id
        self.import_log = "Queuing file for import.\n"
        self.save()

    def get_status(self):
        status = 'PENDING'
        if self.task_id: # pragma: no cover
            result = import_wetmills.AsyncResult(self.task_id)
            status = result.state

        return status

    def log(self, message):
        self.import_log += "%s\n" % message
        self.modified_on = datetime.now()
        self.save()

    class Meta:
        ordering = ('-modified_on',)

def map_columns(cols):
    mapping = dict()

    for (index, col) in enumerate(cols):
        col_name = col.strip().replace('*', '').lower()
        mapping[col_name] = index

    # check all the needed columns are present
    required_cols = ("Name", "Province", "SMS Name", "Year Started", "Latitude", "Longitude", "Altitude")
    for required in required_cols:
        if not required.lower() in mapping.keys():
            raise Exception("CSV file missing the header column '%s', make sure it contains one column each for: %s.  Header was: %s" % (required, ", ".join(required_cols), ",".join(cols)))

    return mapping

def get_row_col(row, index):
    if index < len(row):
        value = row[index]
        if value.strip():
            return value
        else:
            return None

def get_province(country, name):
    try:
        return Province.objects.get(country=country, name=name.strip())
    except:
        raise Exception("Unable to find province '%s' in %s, please make sure it exists" % (name, country.name))

def parse_decimal_value(value):
    if not value or not value.strip():
        return None

    return Decimal(value)

def read_wetmill_row(country, mapping, row, user):
    kwarg_mapping = dict(name="name", province="province", sms_name="sms name", year_started="year started",
                         latitude="latitude", longitude="longitude", altitude="altitude")

    kwargs = dict()
    for kwarg in kwarg_mapping.keys():
        col_name = kwarg_mapping[kwarg]
        kwargs[kwarg]= get_row_col(row, mapping[col_name])

    # check province
    if not kwargs['province']:
        raise Exception("Missing province for row: %s" % ",".join(row))

    kwargs['province'] = get_province(country, kwargs['province'])

    # sms name
    if not kwargs['sms_name']:
        raise Exception("Missing sms name for row: %s" % ",".join(row))

    # and name
    if not kwargs['name']:
        raise Exception("Missing name for row: %s" % ",".join(row))

    # check decimalness of fields
    for field in ('latitude', 'longitude', 'altitude'):
        try:
            kwargs[field] = parse_decimal_value(kwargs[field])
        except:
            raise Exception("Invalid decimal value '%s' for field '%s' for wetmill '%s'" % (kwargs[field], kwarg_mapping[field], kwargs['name']))

    # does this wetmill already exist?
    existing = Wetmill.objects.filter(country=country, name__iexact=kwargs['name'])
    if existing:
        wetmill = existing[0]
        wetmill.province = kwargs['province']
        wetmill.sms_name = kwargs['sms_name']
        wetmill.year_started = kwargs['year_started']
        wetmill.latitude = kwargs['latitude']
        wetmill.longitude = kwargs['longitude']
        wetmill.altitude = kwargs['altitude']
        wetmill.save()
        return wetmill
    else:
        # try to create the wetmill
        return Wetmill.objects.create(country=country, created_by=user, modified_by=user, **kwargs)

def import_csv_wetmills(country, csv_file, user):
    from django.db import transaction
    transaction.commit()
    wetmills = []

    try:
        rows = []
        reader = csv.reader(open(csv_file, 'rU'))
        for row in reader:
            rows.append(row)

        mapping = map_columns(rows[0])

        for row in rows[1:]:
            wetmills.append(read_wetmill_row(country, mapping, row, user))
    except Exception as e:
        # if an errors occurs, roll back any part of our import
        transaction.rollback()
        raise e

    return wetmills
