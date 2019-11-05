from django.test import TestCase

from django.test import TestCase
from django.conf import settings

from datetime import datetime, date
from rapidsms_xforms.models import XForm
from rapidsms_httprouter.models import Message
from django.core.urlresolvers import reverse

from wetmills.models import Wetmill
from .models import *
from sms.models import *
from ..tests import TNSTestCase
import pytz

class DashboardTest(TNSTestCase):

    def create_ibitumbwe(self, wetmill, report_day,
                         cash_advanced, cash_returned, cash_spent, credit_spent,
                         cherry_purchased, credit_cleared):

        IbitumbweSubmission.objects.create(accountant=self.accountant,
                                           wetmill=wetmill,
                                           season=self.season,
                                           report_day=report_day,
                                           active=True,
                                           cash_advanced=cash_advanced,
                                           cash_returned=cash_returned,
                                           cash_spent=cash_spent, 
                                           credit_spent=credit_spent,
                                           cherry_purchased=cherry_purchased,
                                           credit_cleared=credit_cleared)

    def create_sitoki(self, wetmill, start_of_week,
                      grade_a_stored, grade_b_stored, grade_c_stored, 
                      grade_a_shipped, grade_b_shipped, grade_c_shipped):

        SitokiSubmission.objects.create(accountant=self.accountant,
                                        wetmill=wetmill,
                                        season=self.season,
                                        start_of_week=start_of_week,
                                        active=True,
                                        grade_a_stored=grade_a_stored,
                                        grade_b_stored=grade_b_stored,
                                        grade_c_stored=grade_c_stored,
                                        grade_a_shipped=grade_a_shipped,
                                        grade_b_shipped=grade_b_shipped,
                                        grade_c_shipped=grade_c_shipped)

    def test_stock_data(self):
        self.create_connections()
        self.season = self.rwanda_2010
        self.accountant = Accountant.objects.create(connection=self.conn2, name="Nic", wetmill=self.nasho)

        # calculating stats on season without any data should be fine
        wetmills = [self.nasho, self.coko]

        # test our filtering
        (active, inactive) = find_active_wetmills(self.season, wetmills)

        # report in may
        today = date(day=9, month=5, year=2011)

        # none active yet
        self.assertEquals(0, len(active))
        self.assertEquals(2, len(inactive))

        (fields, data) = build_stock_data(self.season, wetmills, today, self.admin)

        # we should have 6 fields
        self.assertEquals(6, len(fields))

        # we should have two wetmills
        self.assertEquals(2, len(data))

        report_day = date(day=7, month=5, year=2011)
        kwargs = dict(wetmill=self.nasho, report_day=report_day,
                      cash_advanced=Decimal(0), cash_returned=Decimal(0), 
                      cash_spent=Decimal(0), credit_spent=Decimal(0),
                      cherry_purchased=Decimal(100), credit_cleared=Decimal(0))
        self.create_ibitumbwe(**kwargs)

        report_day = date(day=8, month=5, year=2011)
        kwargs = dict(wetmill=self.nasho, report_day=report_day,
                      cash_advanced=Decimal(0), cash_returned=Decimal(0), 
                      cash_spent=Decimal(0), credit_spent=Decimal(0),
                      cherry_purchased=Decimal(100), credit_cleared=Decimal(0))
        self.create_ibitumbwe(**kwargs)

        start_of_week = date(day=6, month=5, year=2011)
        kwargs = dict(wetmill=self.nasho, start_of_week=start_of_week, 
                      grade_a_stored=Decimal(1), grade_b_stored=Decimal(1), grade_c_stored=Decimal(1),
                      grade_a_shipped=Decimal(2), grade_b_shipped=Decimal(2), grade_c_shipped=Decimal(2))
        self.create_sitoki(**kwargs)

        (fields, data) = build_stock_data(self.season, wetmills, today, self.admin)

        # first item should be nasho
        wetmill_data = data[0]
        self.assertEquals(self.nasho, wetmill_data['wetmill'])
        self.assertEquals(Decimal(100), wetmill_data['cherry_last'])
        self.assertEquals(Decimal(200), wetmill_data['cherry_ytd'])
        self.assertEquals(Decimal(6), wetmill_data['parchment_shipped_ytd'])
        self.assertEquals(Decimal(3), wetmill_data['parchment_stored_ytd'])
        self.assertDecimalEquals(Decimal("35.46"), wetmill_data['est_parchment_tabled'])
        self.assertDecimalEquals(Decimal("38.46"), wetmill_data['est_parchment_processed'])

    def test_views(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()
        self.accountant = Accountant.objects.create(connection=self.conn2, name="Nic", wetmill=self.nasho)

        # create our projected output
        outputs = []
        outputs.append(PredictedOutput.objects.create(season=self.season, week=1, percentage=10,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=self.season, week=2, percentage=40,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=self.season, week=3, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=self.season, week=4, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))

        # view our stock dashboard
        response = self.client.get(reverse('dashboard.wetmill_dashboard'))

        # nothing to see as a normal user
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        response = self.client.get(reverse('dashboard.wetmill_dashboard') + "?season=%d" % self.season.id)

        # shouldn't be any wetmills yet
        self.assertEquals(0, len(response.context['wetmill_data']))

        # add some submissions for nasho and coko
        report_day = date(day=7, month=5, year=2011)
        kwargs = dict(wetmill=self.nasho, report_day=report_day,
                      cash_advanced=Decimal(0), cash_returned=Decimal(0), 
                      cash_spent=Decimal(0), credit_spent=Decimal(0),
                      cherry_purchased=Decimal(100), credit_cleared=Decimal(0))
        self.create_ibitumbwe(**kwargs)

        kwargs['report_day'] = date(day=14, month=5, year=2011)
        self.create_ibitumbwe(**kwargs)

        report_day = date(day=7, month=5, year=2011)
        kwargs['wetmill'] = self.coko
        self.create_ibitumbwe(**kwargs)

        # two wetmills now
        response = self.client.get(reverse('dashboard.wetmill_dashboard'))
        self.assertEquals(2, len(response.context['wetmill_data']))
        self.assertEquals(self.coko, response.context['wetmill_data'][0]['wetmill'])
        
        # reverse order
        response = self.client.get(reverse('dashboard.wetmill_dashboard') + "?_order=-wetmill")
        self.assertEquals(2, len(response.context['wetmill_data']))
        self.assertEquals(self.nasho, response.context['wetmill_data'][0]['wetmill'])

        # change our outputs for the season
        assumptions = Assumptions.get_or_create(self.season, None, None, self.admin)
        response = self.client.get(reverse('dashboard.assumptions_output', args=[assumptions.id]))
        self.assertEquals(200, response.status_code)

        # now post it, wrong total so will fail
        post_data = dict(week_1=50, week_2=30)
        response = self.client.post(reverse('dashboard.assumptions_output', args=[assumptions.id]), post_data)
        self.assertTrue(response.context['form'].errors)

        # now post to it
        post_data = dict(week_1=50, week_2=50)
        response = self.client.post(reverse('dashboard.assumptions_output', args=[assumptions.id]), post_data)
        self.assertEquals(302, response.status_code)

        # assert our outputs changed
        self.assertEquals(2, PredictedOutput.objects.filter(season=self.season).count())

        # go try to change our assumptions for this season
        response = self.client.get(reverse('dashboard.assumptions_change') + "?season=%d" % self.season.id)
        self.assertRedirect(response, reverse('dashboard.assumptions_update', args=[assumptions.id]))

        response = self.client.get(reverse('dashboard.assumptions_update', args=[assumptions.id]))
        self.assertEquals(200, response.status_code)

        # make sure our form doesn't have csp or wetmill fields since these are season assumptions
        self.assertFalse('csp' in response.context['fields'])
        self.assertFalse('wetmill' in response.context['fields'])

        # change these assumptions to apply to rtc
        assumptions.csp = self.rtc
        assumptions.save()
        response = self.client.get(reverse('dashboard.assumptions_update', args=[assumptions.id]))
        self.assertEquals(200, response.status_code)
        self.assertTrue('csp' in response.context['fields'])
        self.assertFalse('wetmill' in response.context['fields'])

        # make sure a change based on csp takes us to this assumption
        response = self.client.get(reverse('dashboard.assumptions_change') + "?season=%d&csp=%d" % (self.season.id, self.rtc.id))
        self.assertRedirect(response, reverse('dashboard.assumptions_update', args=[assumptions.id]))

        # finally change to a wetmill
        assumptions.csp = None
        assumptions.wetmill = self.nasho
        assumptions.save()
        response = self.client.get(reverse('dashboard.assumptions_update', args=[assumptions.id]))
        self.assertEquals(200, response.status_code)
        self.assertTrue('wetmill' in response.context['fields'])
        self.assertFalse('csp' in response.context['fields'])

        response = self.client.get(reverse('dashboard.assumptions_change') + "?season=%d&wetmill=%d" % (self.season.id, self.nasho.id))
        self.assertRedirect(response, reverse('dashboard.assumptions_update', args=[assumptions.id]))

    def test_assumptions(self):
        season = self.rwanda_2010        

        # no assumptions exist yet, but this should create a default one
        season_assumptions = Assumptions.get_or_create(season, None, None, self.admin)
        season_assumptions.target = 2000
        season_assumptions.save()
        
        # if we try to load again, we should get the same one again
        self.assertEquals(season_assumptions, Assumptions.get_or_create(season, None, None, self.admin))

        # try to load off a csp, should have default of the season
        csp_assumptions = Assumptions.get_or_create(season, self.rtc, None, self.admin)

        # it is a different object
        self.assertFalse(season_assumptions.pk == csp_assumptions.pk)

        # set the defaults on it
        csp_assumptions.set_defaults(season_assumptions)

        # but has the same values as our season assumptions
        self.assertEquals(season_assumptions.target, csp_assumptions.target)

        csp_assumptions.target = 3000
        csp_assumptions.save()

        # now a wetmill
        wetmill_assumptions = Assumptions.get_or_create(season, self.rtc, self.nasho, self.admin)

        # it is a different object
        self.assertFalse(wetmill_assumptions.pk == csp_assumptions.pk)

        wetmill_assumptions.set_defaults(csp_assumptions)

        # but has the same values as our season assumptions
        self.assertEquals(wetmill_assumptions.target, csp_assumptions.target)

    def test_calculated_week(self):
        """
        Tests our projected cherry calculations.
        """
        season = self.rwanda_2010

        # create our projected output
        outputs = []
        outputs.append(PredictedOutput.objects.create(season=season, week=1, percentage=10,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=2, percentage=40,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=3, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=4, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))

        from datetime import date
        start = date(2011, 3, 15)

        season_assumptions = Assumptions.objects.create(season=season,
                                                        target=1000,
                                                        cherry_parchment_ratio=Decimal("1.0"),
                                                        parchment_green_ratio=Decimal("1.0"),
                                                        green_price_differential=Decimal("0.0"),
                                                        season_start=date(day=1, month=5, year=2011),
                                                        season_end=date(day=27, month=5, year=2011),
                                                        parchment_value=Decimal("5.20"),
                                                        created_by=self.admin,
                                                        modified_by=self.admin)

        coko_assumptions = Assumptions.objects.create(season=season,
                                                      wetmill=self.coko,
                                                      target=1000,
                                                      cherry_parchment_ratio=Decimal("1.0"),
                                                      parchment_green_ratio=Decimal("1.0"),
                                                      green_price_differential=Decimal("0.0"),
                                                      season_start=date(day=24, month=4, year=2011),
                                                      season_end=date(day=3, month=6, year=2011),
                                                      parchment_value=Decimal("5.20"),
                                                      created_by=self.admin,
                                                      modified_by=self.admin)

        wetmills = []
        wetmills.append(dict(wetmill=self.nasho, assumptions=season_assumptions))
        wetmills.append(dict(wetmill=self.coko, assumptions=coko_assumptions))

        cherry = calculate_predicted_cherry_curve(season, wetmills)

        self.assertEquals(8, len(cherry))
        self.assertDecimalEquals(0, cherry[0][1])
        self.assertDecimalEquals("66.67", cherry[1][1])
        self.assertDecimalEquals("266.67", cherry[2][1])
        self.assertDecimalEquals("666.67", cherry[3][1])
        self.assertDecimalEquals("416.67", cherry[4][1])
        self.assertDecimalEquals("416.67", cherry[5][1])
        self.assertDecimalEquals("166.67", cherry[6][1])
        self.assertDecimalEquals(0, cherry[7][1])

        coko_assumptions.season_start = date(day=8, month=5, year=2011)
        coko_assumptions.save()

        wetmills = []
        wetmills.append(dict(wetmill=self.nasho, assumptions=season_assumptions))
        wetmills.append(dict(wetmill=self.coko, assumptions=coko_assumptions))

        cherry = calculate_predicted_cherry_curve(season, wetmills)

        self.assertEquals(7, len(cherry))
        self.assertDecimalEquals(0, cherry[0][1])
        self.assertDecimalEquals("100", cherry[1][1])
        self.assertDecimalEquals("500", cherry[2][1])
        self.assertDecimalEquals("650", cherry[3][1])
        self.assertDecimalEquals("500", cherry[4][1])
        self.assertDecimalEquals("250", cherry[5][1])
        self.assertDecimalEquals("0", cherry[6][1])

    def test_projected_cherry_on_day(self):
        season = self.season

        outputs = []
        outputs.append(PredictedOutput.objects.create(season=season, week=1, percentage=10,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=2, percentage=40,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=3, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=4, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))


        # no cherry before season starts
        self.assertEquals(0, calculate_projected_cherry_on_day(-1, 28, 1000, outputs))
        self.assertEquals(0, calculate_projected_cherry(-1, 28, 1000, outputs))

        # no cherry after season ends
        self.assertEquals(0, calculate_projected_cherry_on_day(30, 28, 1000, outputs))
        self.assertEquals(1000, calculate_projected_cherry(30, 28, 1000, outputs))

        # 0th day should bring in 1/7th of 10%
        self.assertDecimalEquals("14.29", calculate_projected_cherry_on_day(0, 28, 1000, outputs))

        # sum of first 7 days should be 100
        week_total = 0
        for i in range(7):
            week_total += calculate_projected_cherry_on_day(i, 28, 1000, outputs)
        self.assertDecimalEquals("100", week_total)

        # sum of total season should be 1000
        season_total = 0
        for i in range(28):
            day = calculate_projected_cherry_on_day(i, 28, 1000, outputs)
            season_total += day
        self.assertDecimalEquals("1000", season_total)

        # ok, let's scale to an eight week season

        # 0th day should bring in 1/7th of 5%
        self.assertDecimalEquals("7.14", calculate_projected_cherry_on_day(0, 56, 1000, outputs))

        # sum of first 7 days should be 50
        week_total = 0
        for i in range(7):
            week_total += calculate_projected_cherry_on_day(i, 56, 1000, outputs)
        self.assertDecimalEquals("50", week_total)

        # sum of total season should be 1000
        season_total = 0
        for i in range(56):
            season_total += calculate_projected_cherry_on_day(i, 56, 1000, outputs)
        self.assertDecimalEquals("1000", season_total)

        # ok, let's scale to two week season

        # 0th day should bring in 1/7th of 20%
        self.assertDecimalEquals("28.57", calculate_projected_cherry_on_day(0, 14, 1000, outputs))

        # sum of first 7 days should be 500
        week_total = 0
        for i in range(7):
            day = calculate_projected_cherry_on_day(i, 14, 1000, outputs)
            week_total += day
        self.assertDecimalEquals("500", week_total)

        # sum of total season should be 1000
        season_total = 0
        for i in range(14):
            season_total += calculate_projected_cherry_on_day(i, 14, 1000, outputs)
        self.assertDecimalEquals("1000", season_total)


    def test_predicted_cherry_curve(self):
        season = self.season

        outputs = []
        outputs.append(PredictedOutput.objects.create(season=season, week=1, percentage=10,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=2, percentage=40,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=3, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))
        outputs.append(PredictedOutput.objects.create(season=season, week=4, percentage=25,
                                                      created_by=self.admin, modified_by=self.admin))


        start = date(day=1, month=5, year=2011)
        curve = calculate_wetmill_predicted_cherry_curve(start, 28, 1000, outputs)

        self.assertEquals(6, len(curve))
        self.assertEquals(0, curve[0][1])
        self.assertEquals(100, curve[1][1])
        self.assertEquals(400, curve[2][1])
        self.assertEquals(250, curve[3][1])
        self.assertEquals(250, curve[4][1])
        self.assertEquals(0, curve[5][1])

        # extra week
        start = date(day=1, month=5, year=2011)
        curve = calculate_wetmill_predicted_cherry_curve(start, 35, 1000, outputs)

        self.assertEquals(7, len(curve))
        self.assertDecimalEquals('0', curve[0][1])
        self.assertDecimalEquals('80', curve[1][1])
        self.assertDecimalEquals('260', curve[2][1])
        self.assertDecimalEquals('260', curve[3][1])
        self.assertDecimalEquals('200', curve[4][1])
        self.assertDecimalEquals('200', curve[5][1])
        self.assertEquals(0, curve[6][1])

        # half an extra week
        curve = calculate_wetmill_predicted_cherry_curve(start, 40, 1000, outputs)

        self.assertEquals(8, len(curve))
        self.assertDecimalEquals('0', curve[0][1])
        self.assertDecimalEquals('70', curve[1][1])
        self.assertDecimalEquals('190', curve[2][1])
        self.assertDecimalEquals('265', curve[3][1])
        self.assertDecimalEquals('175', curve[4][1])
        self.assertDecimalEquals('175', curve[5][1])
        self.assertDecimalEquals('125', curve[6][1])
        self.assertDecimalEquals('0', curve[7][1])

    def test_ideal_submission_count(self):
        season_start = date(day=27, month=2, year=2013)
        today = date(day=6, month=3, year=2013)
        self.nasho.set_accounting_for_season(self.season, '2012')

        self.assertEquals(10, calculate_ideal_submission_count(self.season, self.nasho, season_start, today))

    def test_nyc_price(self):
        price = NYCherryPrice.lookup_nyc_price()

        self.assertTrue(price > Decimal("2.00"))
        self.assertTrue(price < Decimal("5.00"))

    def test_price_recommendation(self):
        price = NYCherryPrice.objects.create(date=datetime.today(), price=Decimal("3.68"),
                                             created_by=self.admin, modified_by=self.admin)

        recommended = price.calculate_recommended_price(Decimal("-0.13"), Decimal("1.64"), Decimal("6.73"), Decimal("600"))
        self.assertDecimalEquals(Decimal("170.28"), recommended)


