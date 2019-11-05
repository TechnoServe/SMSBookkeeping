import pytz
from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _

import logging
logger = logging.getLogger(__name__)

def get_valid_reporter_types():
    """
    Returns all ContentTypes which have a 'connection' field.
    """
    ids = []

    try:
        for content_type in ContentType.objects.all():
            model = content_type.model_class()
            if getattr(model, 'connection', None):
                ids.append(content_type.id)

    except DatabaseError:
        # this is probably occurring during an initial syncdb, where ContentType doesn't even
        # exist yet.  We ignore it for that reason
        pass

    return ids

class Report(models.Model):
    """
    This just encapsultes the text for a report that is sent out.  Conceptually these
    are very similar to CC's, just without a Form triggering them
    """
    name = models.CharField(max_length=100, verbose_name=_("Name"), help_text=_("The name shown to the user when editing responses"))
    description = models.TextField(verbose_name=_("Description"), help_text=_("The description shown to the user when editing responses"))
    day_choices = (('MON', _('Monday')), ('TUE', _('Tuesday')), ('WED', _('Wednesday')),
                                    ('THU', _('Thursday')), ('FRI', _('Friday')), ('SAT', _('Saturday')),
                                    ('SUN', _('Sunday')), ('ALL', _('Everyday')))
    
    slug = models.SlugField(verbose_name=_("Slug"), help_text=_("Slug to identity this report, used to tie this object to a calling function."))
    reporter_types = models.ManyToManyField(ContentType, verbose_name=_("Reporter Types"),
                                            help_text=_("What reporter types should receive this report, optional and up to the calling function to use."))
#                                            limit_choices_to=dict(id__in=get_valid_reporter_types()))
    day = models.CharField(max_length=3, 
                           choices=day_choices, verbose_name=_("Day"),
                           help_text=_("On what day we should send this report."))
    hour = models.IntegerField(verbose_name=_("Hour"), help_text=_("At what hour we should send the report. (0-23)"))
    message = models.CharField(max_length=255, verbose_name=_("Message"), help_text=_("The message to be sent, can include template variables."))
    active = models.BooleanField(default=True, verbose_name=_("Active"), help_text=_("Whether this report is active."))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))

    def __unicode__(self):
        return "%s (%s)" % (self.slug, self.message)

    def get_schedule(self):
        """
        Get's the schedule of when this report is to be sent
        in human readable terms
        """
        for choice in self.day_choices:
            if (choice[0] == self.day):
                day = choice[1]

        return "%s at %d:00" % (day, self.hour)

    # this map maintains our slug->callback functions
    _callbacks = {}    

    def is_send_time(self, utc_time):
        """
        Returns whether this report should be sent.  This uses the passed in time
        to determine whether the check day and hour corresponds appropriately.

        The passed in time must be in UTC, build it using:
                    import pytz
                    utc_time = datetime.now(pytz.utc)
        """
        # we need to look up the timezone for our site in order to convert the passed in time
        # to that timezone
        tzname = settings.USER_TIME_ZONE

        # load our timezone
        tz = pytz.timezone(tzname)

        # change the passed in date to 'local' time for this site
        local = utc_time.astimezone(tz)

        # get our current day of the week
        current_day = local.strftime("%a").upper()

        # only trigger reminders on the appropriate day
        if self.day == 'ALL' or current_day == self.day:
            # return whether the hours are the same
            return local.hour == self.hour

        else:
            # different days?  no reminder
            return False

    def trigger(self):
        """
        Triggers a report to be sent.  We first look up our callback, then call it.
        """
        if not self.slug in Report._callbacks:
            logger.error("Unable to find callback function for report '%s'" % self.slug)
            return False

        else:
            callback = Report._callbacks[self.slug]
            callback(self)
            return True

    @classmethod
    def register(cls, slug, callback):
        """
        Register the callback method for the report with the passed in slug.  The callback will be called
        when the report is to be run, with itself as the arguments.  The responsibility of sending the
        report is up to the called method.
        """
        # just save it away in our map
        Report._callbacks[slug] = callback


    @classmethod
    def check_all(cls, time, quiet=True):
        """
        Runs through all our active reports, sending all that are to be triggered.  This expects
        to be handed a time in UTC timezone, eg:
        
                    import pytz
                    utc_time = datetime.now(pytz.utc)
        """
        sent_count = 0

        # for each active report
        for report in Report.objects.filter(active=True):
            # if it is time to send it off
            if report.is_send_time(time):
                # then do so
                if report.trigger():
                    if not quiet: print "%s - sent" % report.name
                    sent_count += 1
                else:
                    if not quiet: print "%s - not sent, no callback" % report.name

            else:
                if not quiet: print "%s - not time" % report.name

        return sent_count

                    
    

    
