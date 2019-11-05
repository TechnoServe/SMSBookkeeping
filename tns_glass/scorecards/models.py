from smartmin.models import *
from wetmills.models import Wetmill
from seasons.models import Season
from standards.models import Standard, StandardCategory
from django.utils.translation import ugettext_lazy as _

class ScorecardFinalizeException(Exception):
    def __init__(self, fields):
        msg = 'Unable to finalize scorecard due to missing field values. Please fill out these fields and try again: %s' % ", ".join(fields)
        super(ScorecardFinalizeException, self).__init__(msg)

class Scorecard(SmartModel):
    season = models.ForeignKey(Season, related_name='scorecards', verbose_name=_("Season"),
                               help_text=_("The season this scorecard is summarizing"))
    wetmill = models.ForeignKey(Wetmill, related_name='scorecards', verbose_name=_("Wetmill"),
                                help_text=_("The wetmill that this scorecard is being prepared for"))
    client_id = models.CharField(max_length=64, null=True, blank=True, verbose_name=_("Client ID"),
                                help_text=_("The client ID"))
    auditor = models.CharField(max_length=64, null=True, blank=True, verbose_name=_("Auditor"),
                                help_text=_("The auditor of this scorecard"))
    audit_date = models.DateField(null=True, blank=True, verbose_name=_("Audit Date"),
                                help_text=_("The audit date of this scorecard"))
    is_finalized = models.BooleanField(default=False, verbose_name=_("Is Finalized"),
                                    help_text=_("Whether this scorecard's entries have been finalized"))
    rating = models.IntegerField(max_length=1, null=True, blank=True, verbose_name=_("Rating"),
                                 help_text=_("Contains the calculated value of the scorecard ratings"))


    def entries_for_season_standards(self, category = None):
        season_standards = []

        if category:
            standards = self.season.standards.filter(category=category)
        else:
            standards = self.season.standards.all()

        for standard in standards:
            standard_entry = dict(standard=standard, value=None)
            scorecard_entry = self.standard_entries.filter(standard=standard)
            if len(scorecard_entry) > 0 and scorecard_entry[0].value is not None:
                standard_entry['value'] = scorecard_entry[0].value
                season_standards.append(standard_entry)

        return season_standards

    @classmethod
    def get_for_wetmill_season(cls, wetmill, season, user):
        # try to look up an existing scorecard
        existing = Scorecard.objects.filter(wetmill=wetmill, season=season)
        if existing:
            return existing[0]
        else:
            return Scorecard.objects.create(wetmill=wetmill, season=season, created_by=user, modified_by=user)

    def calculate_category_metrics(self, standard_category):
        """
        Calculates metrics for this category in standard categories for this scorecard. The scorecard must be finalized
        """
        entries = self.entries_for_season_standards(standard_category)
        count = len(entries)

        minimum = []
        min_count = 0
        best = 0
        best_count = 0

        for entry in entries:
            if entry['standard'].kind == 'MR':
                min_count += 1
                minimum.append('YES') if entry['value'] == 100 else minimum.append('NO')
            elif entry['standard'].kind == 'BP':
                best_count += 1
                best += entry['value']

        all_minimum = ''

        if min_count == 0:
            all_minimum = 'N/A'
        else:
            all_minimum = 'YES' if 'NO' not in minimum else 'NO'

        if best_count > 0:
            best_percentage = best/best_count
        else:
            best_percentage = 100

        return (all_minimum, best_percentage)

    def calculate_metrics(self):
        scorecard_metrics = dict()
        for category in StandardCategory.objects.all():
            scorecard_metrics[category.acronym] = self.calculate_category_metrics(category)
            
        return scorecard_metrics

    def get_rating(self):
        """
        From metrics please decide which award to give
        """
        all_minimum = 0
        best_less_40 = 0
        best_greater_40 = 0
        best_greater_60 = 0
        best_greater_80 = 0

        values = self.calculate_metrics()
        count = len(values)

        for category in values.keys():
            if values[category][0] != 'NO':
                all_minimum += 1
            if values[category][1] >= 80:
                best_greater_80 += 1
            if values[category][1] >= 60:
                best_greater_60 += 1
            if values[category][1] >= 40:
                best_greater_40 += 1
            else:
                best_less_40 += 1

        if all_minimum == count:
            if best_greater_80 == count:
                return 5
            elif best_greater_60 == count:
                return 4
            elif best_greater_40 == count:
                return 3
            elif best_less_40 > 0:
                return 2
        else:
            return 1

    def finalize(self):
        empty_fields = []
        season_entries = self.entries_for_season_standards()

        for entry in season_entries:
            # less than zero for choice field null means -1
            if entry['value'] is None or entry['value'] < 0:
                empty_fields.append(entry['standard'].name)

        # more than one missing value, raise an exception
        if len(empty_fields) > 0:
            raise ScorecardFinalizeException(empty_fields)

        # ok, all good, mark ourselves as finalized
        self.is_finalized = True
        self.save()
        self.calculate_metrics()

        # save ratings as the scorecard has been finalized
        self.rating = self.get_rating()

    def add_entry(self, standard, value, user):
        StandardEntry.objects.filter(scorecard=self, standard=standard).delete()
        return StandardEntry.objects.create(scorecard=self, standard=standard, value=value,
                                            created_by=user, modified_by=user)

    def __unicode__(self):
        return '%s %s Scorecard' % (self.season.name, self.wetmill.name)

class StandardEntry(SmartModel):
    scorecard = models.ForeignKey(Scorecard, related_name='standard_entries', verbose_name=_("Scorecard"))
    standard = models.ForeignKey(Standard, related_name='standard_entries', verbose_name=_("Standard"),
                                help_text=_("The standard that we are recording the value for"))
    value = models.IntegerField(null=True, blank=True, verbose_name=_("Value"),
                                help_text=_("The value of the standard for this wetmill and season"))

    def __unicode__(self):
        if self.value is None:
            return '%s' % self.standard.name
        else:
            return '%s - %s' % (self.standard.name, self.value)

    class Meta:
        unique_together = ('scorecard', 'standard')
        ordering = ('standard__category','standard__order')

class ScorecardAmendments(SmartModel):
    scorecard = models.ForeignKey(Scorecard, related_name="amendments", verbose_name=_("Scorecard"))
    description = models.TextField(verbose_name=_("Description"))
