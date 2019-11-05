from django.db import models
from smartmin.models import SmartModel

from sms.models import *
from wetmills.models import Wetmill
from csps.models import CSP
from locales.models import Country
from seasons.models import Season

from rapidsms_httprouter.router import get_router
from rapidsms_httprouter.models import Message
from reports.models import Report
from aggregates.models import ReportValue, SeasonMetric

from django.db.models import Sum
from datetime import timedelta

from django.utils.translation import ugettext_lazy as _
from django.template import Context, Template

class Broadcast(SmartModel):
    RECIPIENT_CHOICES = (('F', "Farmers"),
                         ('A', "Accountants"),
                         ('O', "Observers"))

    recipients = models.CharField(max_length=16, verbose_name=_("Recipients"))

    country = models.ForeignKey(Country, verbose_name=_("Country"),
                                help_text="Only include wetmills in this country")

    wetmills = models.ManyToManyField(Wetmill, verbose_name=_("Wetmills"), null=True, blank=True)
    csps =  models.ManyToManyField(CSP, verbose_name='CSPs', null=True, blank=True)

    exclude_wetmills = models.ManyToManyField(Wetmill, null=True, blank=True, related_name='excluded_broadcasts', verbose_name=_("Exclude Wetmills"),
                                              help_text=_("Exclude these wetmills (leave blank for none)"))
    exclude_csps = models.ManyToManyField(CSP, verbose_name='Exclude CSPs', null=True, blank=True, related_name='excluded_broadcasts',
                                          help_text=_("Exclude wetmills in these CSPs (leave blank for none)"))

    report_season = models.ForeignKey(Season, null=True, blank=True, related_name='report_broadcasts', verbose_name=_("Report Season"),
                                      help_text=_("Only include wetmills with finalized reports in this season (leave blank for all)"))
    sms_season = models.ForeignKey(Season, null=True, blank=True, related_name='sms_broadcasts', verbose_name=_("SMS Season"),
                                   help_text=_("Only include wetmills with SMS accounting messages in this season (leave blank for all)"))

    text = models.TextField(max_length=480, verbose_name=_("Text"))

    send_on = models.DateTimeField(null=True, blank=True, verbose_name=_("Send On"))

    sent = models.BooleanField(default=False, verbose_name=_("Sent"))
    messages = models.ManyToManyField(Message, null=True, blank=True, verbose_name=_("Messages"))

    def __unicode__(self): # pragma: no cover
        return self.text

    def get_recipients_display(self):
        recipients = []
        for (code, name) in Broadcast.RECIPIENT_CHOICES:
            if code in self.recipients:
                recipients.append(name)

        return ",".join(recipients)

    def get_wetmills(self):
        return Broadcast.calculate_wetmills(self.country, self.report_season, self.sms_season,
                                            self.wetmills.all(), self.csps.all(), self.exclude_wetmills.all(), self.exclude_csps.all())

    @classmethod
    def calculate_wetmills(cls, country, report_season, sms_season, only_wetmills, only_csps, exclude_wetmills, exclude_csps):
        """
        Returns all the wetmills that match this broadcast
        """
        wetmills = Wetmill.objects.filter(country=country)
        if only_wetmills:
            wetmills = only_wetmills.filter(country=country)

        # handle excluding wetmills
        if exclude_wetmills:
            wetmills = wetmills.exclude(pk__in=[_.pk for _ in exclude_wetmills])

        if only_csps:
            season = report_season
            if not season: # pragma: no cover
                season = sms_season

            if season:
                wetmills = wetmills.filter(wetmillcspseason__season=season,
                                           wetmillcspseason__csp__in=only_csps)

        # handle excluding certain csps
        if exclude_csps:
            season = report_season
            if not season: # pragma: no cover
                season = sms_season

            if season:
                wetmills = wetmills.exclude(wetmillcspseason__season=season,
                                            wetmillcspseason__csp__in=exclude_csps)

        # filter out only wetmills that have values for this season
        if report_season:
            wetmills = wetmills.filter(pk__in=[_['report__wetmill'] for _ in ReportValue.objects.filter(report__season=report_season).values('report__wetmill').distinct()])

        if sms_season:
            # we only want wetmills which have submitted at least one ibitumbwe, sitoki and amafaranga message
            sitoki_wetmills = [_['wetmill'] for _ in SitokiSubmission.objects.filter(season=sms_season).values('wetmill').distinct()]
            ibitumbwe_wetmills = [_['wetmill'] for _ in IbitumbweSubmission.objects.filter(season=sms_season).values('wetmill').distinct()]
            amafaranga_wetmills = [_['wetmill'] for _ in AmafarangaSubmission.objects.filter(season=sms_season).values('wetmill').distinct()]

            sms_wetmills = set(sitoki_wetmills) & set(ibitumbwe_wetmills) & set(amafaranga_wetmills)
            wetmills = wetmills.filter(pk__in=sms_wetmills)

        return wetmills.order_by('name')

    def add_report_context(self, context, report):
        # plug all our report values into our context
        for value in ReportValue.objects.filter(report=report):
            context[value.metric.slug] = value.value

            # throw in our rank slug
            context["%s__rank" % value.metric.slug] = value.rank()

            # throw in our season slugs
            season_values = value.get_season_values()
            for key in season_values.keys():
                context["%s__%s" % (value.metric.slug, key)] = season_values[key]

    def add_sms_context(self, context, wetmill, now):
        previous_sitoki = SitokiSubmission.objects.filter(season=self.sms_season, wetmill=wetmill, 
                                                          active=True).order_by('-start_of_week')

        sitoki_end = None
        cherry_end = None

        context['sms_cherry_purchased'] = Decimal(0)
        context['sms_parchment_processed'] = Decimal(0)
        context['sms_cherry_to_parchment_ratio'] = Decimal(0)

        if previous_sitoki:
            sitoki_end = previous_sitoki[0].start_of_week
            cherry_end = sitoki_end - timedelta(days=10)

            # get all ibitumbwe submissions that ocurred
            subs = IbitumbweSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                      active=True, report_day__lte=cherry_end)

            # get the sum of cherry purchased
            if subs:
                context['sms_cherry_purchased'] = subs.aggregate(Sum('cherry_purchased'))['cherry_purchased__sum']

            # get all sitoki submissions
            subs = SitokiSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                   active=True, start_of_week__lte=sitoki_end)

            sums = subs.aggregate(Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'))
            if subs:
                context['sms_parchment_processed'] = sums['grade_a_stored__sum'] + sums['grade_b_stored__sum'] + sums['grade_c_stored__sum']

            if context['sms_parchment_processed'] > Decimal(0):
                ratio = context['sms_cherry_purchased'] / context['sms_parchment_processed']
                ratio = ratio.quantize(Decimal(".01"))
                context['sms_cherry_to_parchment_ratio'] = ratio

        subs = AmafarangaSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                   active=True, start_of_week__lte=now)

        casual_labor = Decimal(0)
        context['sms_working_cap'] = Decimal(0)
        context['sms_working_cap_non_cherry_percent'] = Decimal(0)

        if subs:
            sums = subs.aggregate(Sum('working_capital'), Sum('full_time_labor'), Sum('casual_labor'), 
                                  Sum('commission'), Sum('transport'), Sum('other_expenses'))
            working_capital = sums['working_capital__sum']

            context['sms_working_cap'] = working_capital

            non_cherry = sums['full_time_labor__sum'] + sums['casual_labor__sum'] + sums['commission__sum'] + sums['transport__sum'] + sums['other_expenses__sum']

            context['sms_working_cap_non_cherry_percent'] = (non_cherry * Decimal("100") / working_capital).quantize(Decimal("1"))
            casual_labor = sums['casual_labor__sum']

        subs = IbitumbweSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                  active=True, report_day__lte=now)

        context['sms_casual_labor_kgc'] = Decimal(0)
        if subs and casual_labor > Decimal(0):
            cherry_purchased_ytd = subs.aggregate(Sum('cherry_purchased'))['cherry_purchased__sum']

            if cherry_purchased_ytd > Decimal(0):
                context['sms_casual_labor_kgc'] = (casual_labor / cherry_purchased_ytd).quantize(Decimal(".01"))

        subs = IbitumbweSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                  active=True, report_day__lte=now).order_by('-report_day')
        if subs:
            context['last_ibitumbwe_submission'] = subs[0].report_day
        else:
            context['last_ibitumbwe_submission'] = None

        subs = SitokiSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                               active=True, start_of_week__lte=now).order_by('-start_of_week')
        if subs:
            context['last_sitoki_submission'] = subs[0].start_of_week
        else:
            context['last_sitoki_submission'] = None

        subs = AmafarangaSubmission.objects.filter(season=self.sms_season, wetmill=wetmill,
                                                  active=True, start_of_week__lte=now).order_by('-start_of_week')
        if subs:
            context['last_amafaranga_submission'] = subs[0].start_of_week
        else:
            context['last_amafaranga_submission'] = None

        context['today'] = now

    def render(self, wetmill, actor, now):
        """
        Renders this template for the passed in actor
        """
        total_wetmills = len(self.get_wetmills())
        context = dict(wetmill=wetmill, actor=actor, total_wetmills=total_wetmills)

        # if we have a finalized report, and the season is finalized
        if self.report_season and self.report_season.is_finalized:
            report = Report.get_for_wetmill_season(wetmill, self.report_season)
            if report and report.is_finalized:
                self.add_report_context(context, report)

        # if we are an SMS message, insert those variables
        if self.sms_season:
            self.add_sms_context(context, wetmill, now)

        t = Template(self.text)
        return t.render(Context(context)).strip()

    def get_recipients_for_wetmill(self, wetmill):
        """
        Returns all the recipients for the passed in wetmill
        """
        recipients = list()
        connections = set()

        if self.recipients.find('A') >= 0:
            for accountant in Accountant.objects.filter(wetmill=wetmill, active=True):
                if not accountant.connection in connections:
                    recipients.append(accountant)
                    connections.add(accountant.connection)

        if self.recipients.find('F') >= 0:
            for farmer in Farmer.objects.filter(wetmill=wetmill, active=True):
                if not farmer.connection in connections:
                    recipients.append(farmer)
                    connections.add(farmer.connection)

        if self.recipients.find('O') >= 0:
            for observer in WetmillObserver.objects.filter(wetmill=wetmill, active=True):
                if not observer.connection in connections:
                    recipients.append(observer)
                    connections.add(observer.connection)

        return recipients

    @classmethod
    def get_pending(self, now):
        """
        Gets all broadcasts that need to be sent according to the current date
        """
        return Broadcast.objects.filter(sent=False, send_on__lte=now)

    def send(self):
        """
        send the message to all connections linked to a broadcast object 
        """
        router = get_router()
        now = datetime.now()

        for wetmill in self.get_wetmills():
            recipients = self.get_recipients_for_wetmill(wetmill)

            # for each recipient, render the message
            for recipient in recipients:
                try:
                    message_text = self.render(wetmill, recipient, now)

                    # ignore messages that have no content (if statements make this possible)
                    if message_text:
                        db_message = router.add_outgoing(recipient.connection, message_text)
                        self.messages.add(db_message)
                        
                except Exception as e: #pragma: no cover
                    print("Error sending broadcast: %d for recipient: %d and wetmill %d" %
                          (self.id, recipient.id, wetmill.id), e)

        self.sent = True
        self.save()

    def add_report_variables(self, variables):
        variables.append(dict(slug='total_wetmills', label="Number of Wetmills"))
        for metric in SeasonMetric.objects.filter(season=self.report_season):
            variables.append(dict(slug=metric.slug, label=metric.label))

    def add_sms_variables(self, variables):
        curr_code = self.sms_season.country.currency.currency_code

        variables.append(dict(slug='sms_cherry_purchased', label="SMS - Total Cherry Purchased (KgC)"))
        variables.append(dict(slug='sms_parchment_processed', label="SMS - Total Parchment Processed (KgC)"))
        variables.append(dict(slug='sms_cherry_to_parchment_ratio', label="SMS - C:P Ratio"))
        variables.append(dict(slug='sms_working_cap', label="SMS - Total Working Capital (%s)" % curr_code))
        variables.append(dict(slug='sms_working_cap_non_cherry_percent', label="SMS - Working Capital Non Cherry Percentage"))
        variables.append(dict(slug='sms_casual_labor', label="SMS - Total Casual Labor (%s)" % curr_code))
        variables.append(dict(slug='sms_casual_labor_kgc', label="SMS - Total Casual Labor (%s/KgC)" % curr_code))
        variables.append(dict(slug='last_ibitumbwe_submission', label="SMS - Date of last Ibitumbwe Submission"))
        variables.append(dict(slug='last_sitoki_submission', label="SMS - Date of last Sitoki Submission"))
        variables.append(dict(slug='last_amafaranga_submission', label="SMS - Date of last Amafaranga Submission"))
        variables.append(dict(slug='today', label="SMS - Today's Date (when sent)"))


