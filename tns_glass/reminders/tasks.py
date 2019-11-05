from celery.decorators import task
from datetime import datetime, timedelta
from sms.models import get_week_start_before, AmafarangaSubmission, SitokiSubmission, IbitumbweSubmission
from .models import *

@task()
def check_weekly_reminders(now=None):
    if not now:  # pragma: no cover
        now = datetime.now()

    # get our week start
    start_of_week = get_week_start_before(now)

    context = dict()
    context['week_start'] = start_of_week.strftime("%d.%m.%y")
    context['week_end'] = (start_of_week + timedelta(days=6)).strftime("%d.%m.%y")

    print "-- checking Amafaranga reminders"

    # check amafaranga messages
    late_wetmills = get_wetmills_needing_weekly_reminder(start_of_week, AmafarangaSubmission.objects)

    print "-- %d wetmills late" % len(late_wetmills)

    xform = XForm.objects.get(keyword__startswith='amafaranga')
    send_reminders_for_wetmills(xform, late_wetmills, context,
                                "No Amafaranga message received for {{ wetmill.name }} for the week starting {{ week_start }}")

    print "-- checking Sitoki reminders"

    late_wetmills = get_wetmills_needing_weekly_reminder(start_of_week, SitokiSubmission.objects)
    xform = XForm.objects.get(keyword__startswith='sitoki')

    print "-- %d wetmills late" % len(late_wetmills)

    send_reminders_for_wetmills(xform, late_wetmills, context,
                                "No Sitoki message received for {{ wetmill.name }} for the week starting {{ week_start }}")

@task()
def check_daily_reminders(now=None):
    if not now:  # pragma: no cover
        now = datetime.now()

    # we are looking for messages for yesterday
    report_day = now - timedelta(days=1)

    context = dict()
    context['day'] = report_day.strftime("%d.%m.%y")

    print "-- checking Ibitumbwe reminders"

    # check ibitumbwe messages
    late_wetmills = get_wetmills_needing_daily_reminder(report_day)
    xform = XForm.objects.get(keyword__startswith='ibitumbwe')

    print "-- %d wetmills late" % len(late_wetmills)

    send_reminders_for_wetmills(xform, late_wetmills, context,
                                "No Ibitumbwe or Twakinze message received for {{ wetmill.name }} for {{ day }}")
