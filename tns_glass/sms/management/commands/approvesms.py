import traceback
import pytz
from datetime import datetime

from optparse import make_option

from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connections, router, transaction, DEFAULT_DB_ALIAS
from django.db.models import get_apps
from django.utils.itercompat import product
from rapidsms_httprouter.router import get_router
from reports.models import Report
from sms.models import *
import datetime

class Command(BaseCommand):
    """
    This command goes and approves any messages which didn't get any subsequent sends within an hour
    """
    help = 'Checks all our sms reports, triggering approval for any which didnt get subsequent messages within an hour'
    option_list = BaseCommand.option_list + (
        make_option('--quiet',
                    action='store_true',
                    dest='quiet',
                    default=False,
                    help='Only output on errors.'),)

    def approve_message_class(self, clazz):
        three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)

        messages = clazz.all.filter(active=False, created__gte=three_months_ago).order_by('created')
        print "[%s] checking %d message" % (clazz, messages.count())

        count = 0
        for message in messages:
            # is there a message within an hour
            hour_later = message.created + datetime.timedelta(minutes=59)
            if not clazz.all.filter(created__gt=message.created,
                                    created__lt=hour_later,
                                    accountant=message.accountant,
                                    wetmill=message.wetmill):
                # then approve it
                print "unapproved: %s" % message

                # make sure there is an approved ibitumbwe earlier than us
                if ((clazz == TwakinzeSubmission or clazz == IbitumbweSubmission) and IbitumbweSubmission.objects.filter(report_day__lt=message.report_day, wetmill=message.wetmill, season=message.season)) or ((clazz == SitokiSubmission or clazz == AmafarangaSubmission) and IbitumbweSubmission.objects.filter(report_day__lt=message.start_of_week, wetmill=message.wetmill, season=message.season)):

                    if clazz == TwakinzeSubmission:
                        if not IbitumbweSubmission.objects.filter(report_day=message.report_day, wetmill=message.wetmill):
                            print "approving on %s" % message.report_day
                            message.active = True
                            message.is_active = True
                            message.save()
                            count += 1
                        else:
                            print "not approving, ibitumbwe on date"

                    elif clazz == IbitumbweSubmission:
                        if not TwakinzeSubmission.objects.filter(report_day=message.report_day, wetmill=message.wetmill):
                            message.active = True
                            message.is_active = True
                            message.save()                
                            count += 1
                
                    else:
                        message.active = True
                        message.is_active = True
                        message.save()                                    
                        count += 1

        print "[%s] %d approved" % (clazz, count)

    def handle(self, quiet=False, *files, **options):
        connection = connections[DEFAULT_DB_ALIAS]
        self.style = no_style()

        try:
            for clazz in [AmafarangaSubmission, SitokiSubmission, IbitumbweSubmission, TwakinzeSubmission]:
                self.approve_message_class(clazz)

        except Exception as e:
            traceback.print_exc(e)



