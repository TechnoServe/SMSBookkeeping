from datetime import timedelta
from rapidsms_httprouter.router import get_router
from django.utils.translation import trans_real

from sms.models import *
from wetmills.models import WetmillSeasonAccountingSystem


def get_wetmills_needing_daily_reminder(day):
    """
    Returns wetmills which have sent an ibitumbwe or twakinze message in the past three days, but have not
    sent one for the past day.
    """
    # accountants that qualify for reminders are those that have sent a message in the past three days
    three_days_ago = day - timedelta(days=3)

    active_wetmills = set([_.wetmill for _ in IbitumbweSubmission.objects.filter(report_day__gte=three_days_ago).order_by('wetmill')])
    active_wetmills |= set([_.wetmill for _ in TwakinzeSubmission.objects.filter(report_day__gte=three_days_ago).order_by('wetmill')])

    # now get all wetmills which sent an ibitumbwe or twakinze for the specific day
    compliant_wetmills = set([_.wetmill for _ in IbitumbweSubmission.objects.filter(report_day__gte=day).order_by('wetmill')])
    compliant_wetmills |= set([_.wetmill for _ in TwakinzeSubmission.objects.filter(report_day__gte=day).order_by('wetmill')])

    # the wetmills that need notification is those that are not compliant
    return active_wetmills - compliant_wetmills

def get_wetmills_needing_weekly_reminder(week_start, objects):
    """
    Returns the wetmills which need a weekly reminder given the week start.  Callers should pass in the
    the start of the week as well as the object manager for that weekly message
    """
    # we only want to include wetmills which sent an ibitumbwe message since the week start
    active_wetmills = set()
    for submission in IbitumbweSubmission.objects.filter(report_day__gte=week_start).order_by('wetmill'):
        if submission.wetmill.get_accounting_for_season(submission.season) == '2012':
            active_wetmills.add(submission.wetmill)

    # now get all wetmills which sent one of our messages for that week
    compliant_wetmills = set([_.wetmill for _ in objects.filter(start_of_week=week_start).order_by('wetmill')])

    # the wetmills that need notification is those that are not compliant
    return active_wetmills - compliant_wetmills

def send_reminders_for_wetmills(xform, wetmills, context, default_text):
    router = get_router()

    # for each wetmill
    for wetmill in wetmills:
        context['wetmill'] = wetmill

        # send to all accountants
        for accountant in Accountant.objects.filter(wetmill=wetmill):
            # activate our language if there is one
            trans_real.activate(accountant.language)
            text = Blurb.get(xform, 'accountant-reminder', context, default_text)

            # and send it off
            router.add_outgoing(accountant.connection, text)

        # and all observers
        for observer in WetmillObserver.objects.filter(wetmill=wetmill):
            # activate our language if there is one
            trans_real.activate(observer.language)
            text = Blurb.get(xform, 'observer-reminder', context, default_text)

            # and send it off
            router.add_outgoing(observer.connection, text)

    activate('en-us')
