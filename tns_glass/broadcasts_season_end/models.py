from django.db import models
from smartmin.models import SmartModel

from wetmills.models import Wetmill
from seasons.models import Season
from sms.models import Accountant, Farmer, WetmillObserver

from reports.models import Report
from aggregates.models import ReportValue, SeasonMetric

from django.utils.translation import ugettext_lazy as _
from django.template import Context, Template

from rapidsms_httprouter.router import get_router
from rapidsms_httprouter.models import Message

from datetime import datetime


"""
We define a set of messages that are sent out at the end of seasons manually.
The messages are sent out one wetmill at a time.
This essentially contains the templates.
"""


class BroadcastsOnSeasonEnd(SmartModel):
    RECIPIENT_CHOICES = (('F', "Farmers"),
                         ('A', "Accountants"),
                         ('O', "Observers"))
    name = models.CharField(max_length=100, verbose_name=_("End of Season Template name"))
    recipients = models.CharField(max_length=16, verbose_name=_("Recipients"),
                                  help_text=_("Put in F for Farmers, A for accountants and O for Observers."))
    text = models.TextField(max_length=480, verbose_name=_("Text"))
    description = models.TextField(max_length=100, verbose_name=_("Description"))

    messages = models.ManyToManyField(Message, null=True, blank=True, verbose_name=_("Wetmill"))
    wetmills = models.ManyToManyField(Wetmill, null=True, blank=True, verbose_name=_("Wetmill"))
    report_seasons = models.ManyToManyField(Season, null=True, blank=True, verbose_name=_("Report Season"))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'End of Season Message Template'
        verbose_name_plural = 'End of Season Message Templates'

    def get_recipients_for_wetmill(self, wetmill):
        """
        Returns all the recipients for the passed in wetmill
        """
        recipients = list()
        connections = set()

        if self.recipients.find('A') >= 0:
            for accountant in Accountant.objects.filter(wetmill=wetmill, active=True):
                if accountant.connection not in connections:
                    recipients.append(accountant)
                    connections.add(accountant.connection)

        if self.recipients.find('F') >= 0:
            for farmer in Farmer.objects.filter(wetmill=wetmill, active=True):
                if farmer.connection not in connections:
                    recipients.append(farmer)
                    connections.add(farmer.connection)

        if self.recipients.find('O') >= 0:
            for observer in WetmillObserver.objects.filter(wetmill=wetmill, active=True):
                if observer.connection not in connections:
                    recipients.append(observer)
                    connections.add(observer.connection)

        return recipients

    def get_recipients_display(self):
        recipients = []
        for (code, name) in BroadcastsOnSeasonEnd.RECIPIENT_CHOICES:
            if code in self.recipients:
                recipients.append(name)

        return ",".join(recipients)

    @classmethod
    def get_wetmills(cls, country, season):
        return cls.calculate_wetmills(country, season)

    @classmethod
    def calculate_wetmills(cls, country, report_season):
        """
        Returns all the wetmills that match this broadcast
        """
        wetmills = Wetmill.objects.filter(country=country)

        # filter out only wetmills that have values for this season
        if report_season:
            wetmills = wetmills.filter(pk__in=[_['report__wetmill'] for _ in ReportValue.objects.filter(report__season=report_season).values('report__wetmill').distinct()])

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

    def render(self, wetmill, report_season, actor, now):
        """
        Renders this template for the passed in actor
        """
        total_wetmills = len(self.get_wetmills(wetmill.country, report_season))
        context = dict(wetmill=wetmill, actor=actor, total_wetmills=total_wetmills)

        # if we have a finalized report, and the season is finalized
        if report_season and report_season.is_finalized:
            report = Report.get_for_wetmill_season(wetmill, report_season)
            if report and report.is_finalized:
                self.add_report_context(context, report)

        t = Template(self.text)
        return t.render(Context(context)).strip()

    def send(self, wetmill_chosen, season):
        """
        send the message to all connections linked to a broadcast object
        """
        router = get_router()
        now = datetime.now()

        msg_recipients = self.get_recipients_for_wetmill(wetmill_chosen)

        # for each recipient, render the message
        for recipient in msg_recipients:
            try:
                message_text = self.render(wetmill_chosen, season, recipient, now)

                # ignore messages that have no content (if statements make this possible)
                if message_text:
                    db_message = router.add_outgoing(recipient.connection, message_text)
                    self.messages.add(db_message)
                    self.report_seasons.add(season)
                    self.wetmills.add(wetmill_chosen)


            except Exception as e:
                print("Error sending end of season messages: %d for recipient: %d and wetmill %d" %
                      (self.name, recipient.id, wetmill_chosen.id), e)

        self.save()
