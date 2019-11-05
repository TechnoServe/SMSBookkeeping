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
from seasons.models import *
from wetmills.models import *
from locales.models import Country

class Command(BaseCommand):
    """
    This command is responsible for making sure all wetmills have inherited the wetmill
    from the previous season.
    """
    help = 'Checks all our wetmills seasons are fixed'
    option_list = BaseCommand.option_list + (
        make_option('--quiet',
                    action='store_true',
                    dest='quiet',
                    default=False,
                    help='Only output on errors.'),)

    def handle(self, quiet=False, *files, **options):
        connection = connections[DEFAULT_DB_ALIAS]
        self.style = no_style()

        # our current date/time in UTC
        utc_time = datetime.now(pytz.utc)

        for country in Country.objects.all():
            prev = None
            print "== %s" % country.name

            for season in Season.objects.filter(country=country).order_by('name'):
                print "=== %s" % season.name

                if prev is None:
                    prev = season
                    continue

                for wetmill in Wetmill.objects.filter(country=country):
                    csp = wetmill.get_csp_for_season(season)
                    if csp is None:
                        prev_csp = wetmill.get_csp_for_season(prev)
                        if prev_csp:
                            wetmill.set_csp_for_season(season, prev_csp)
                            print "[%s] %s to %s" % (season.name, wetmill.name, prev_csp.name)


                prev = season
                
