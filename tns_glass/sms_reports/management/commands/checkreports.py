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

class Command(BaseCommand):
    """
    This command is responsible for looping through all our reports and sending off all
    of those that are necessary.
    """
    help = 'Checks all our reports, triggering any that are necessary.'
    option_list = BaseCommand.option_list + (
        make_option('--quiet',
                    action='store_true',
                    dest='quiet',
                    default=False,
                    help='Only output on errors.'),)

    def handle(self, quiet=False, *files, **options):
        connection = connections[DEFAULT_DB_ALIAS]
        self.style = no_style()

        cursor = connection.cursor()

        # we do all messages in one transaction
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)

        # our current date/time in UTC
        utc_time = datetime.now(pytz.utc)

        try:
            # check our reports
            sent = Report.check_all(utc_time, quiet)
            if not quiet:
                print
                print "%d reports sent." % sent
        except Exception as e:
            traceback.print_exc(e)
    
        # one uber commit
        transaction.commit()


