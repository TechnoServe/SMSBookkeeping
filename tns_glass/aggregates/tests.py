from django.test import TestCase
from ..tests import TNSTestCase
from reports.tests.base import PDFTestCase
from seasons.models import *
from reports.models import *
from .models import SeasonAggregate, FinalizeTask, ReportValue
from django.core.urlresolvers import reverse

class FinalizeTest(TNSTestCase):

    def setUp(self):
        super(FinalizeTest, self).setUp()
        
        self.season = self.rwanda_2010
        self.configure_season()

    def test_view(self):
        # test permission
        create_url = reverse('aggregates.finalizetask_create')
        response = self.client.get(create_url)
        self.assertRedirect(response, reverse('users.user_login'))
        self.login(self.admin)

        post_data = dict(season=self.season.id)
        response = self.assertPost(create_url, post_data)
        task = FinalizeTask.objects.get()
        self.assertEquals('PENDING', task.get_status())

        task.task_log = ""
        task.save()

        task.log("hello world")
        task = FinalizeTask.objects.get()        
        self.assertEquals("hello world\n", task.task_log)
        self.assertEquals("Finalize Task for 2010", str(task))

        response = self.client.get(reverse('aggregates.finalizetask_read', args=[task.id]))
        self.assertContains(response, "PENDING")

        response = self.client.get(reverse('aggregates.finalizetask_list'))
        self.assertContains(response, "PENDING")

    def test_simple_aggregate(self):
        # not finalized, no report
        self.assertIsNone(self.nasho.report)
        nasho_report = self.generate_report(self.nasho, Decimal("1"))

        # season not finalized, no report
        self.assertIsNone(self.nasho.report)

        SeasonAggregate.calculate_for_season(self.season)

        # should have a report now
        self.assertIsNotNone(self.nasho.report)

        aggs = SeasonAggregate.for_season(self.season)

        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].best)
        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].average)

        self.assertDecimalEquals("40", aggs['expense__%d' % self.expense_washing_station.id].best)
        self.assertDecimalEquals("40", aggs['expense__%d' % self.expense_washing_station.id].average)

        self.assertDecimalEquals("3.6", aggs['expense__%d' % self.expense_capex_interest.id].best)
        self.assertDecimalEquals("3.6", aggs['expense__%d' % self.expense_capex_interest.id].average)

        self.assertDecimalEquals("43.60", aggs['total_expenses'].best)
        self.assertDecimalEquals("43.60", aggs['total_expenses'].average)

        self.assertDecimalEquals("-0.6", aggs['total_forex_loss'].best)
        self.assertDecimalEquals("-0.6", aggs['total_forex_loss'].average)

        self.assertDecimalEquals("10", aggs['cashuse__%d' % self.cu_dividend.id].best)
        self.assertDecimalEquals("10", aggs['cashuse__%d' % self.cu_dividend.id].average)

        self.assertDecimalEquals("200", aggs['farmer__fp__%d__MEM' % self.fp_dividend.id].best)
        self.assertFalse('farmer__fp__%d__NON' % self.fp_dividend.id in aggs)
        self.assertFalse('farmer__fp__%d__ALL' % self.fp_dividend.id in aggs)

        self.assertDecimalEquals("200", aggs['farmer__fp__%d__MEM' % self.fp_dividend.id].average)
        self.assertFalse('farmer__fp__%d__NON' % self.fp_dividend.id in aggs)
        self.assertFalse('farmer__fp__%d__ALL' % self.fp_dividend.id in aggs)

        self.assertDecimalEquals("15", aggs['cashuse__%d' % self.cu_second_payment.id].best)
        self.assertDecimalEquals("15", aggs['cashuse__%d' % self.cu_second_payment.id].average)

        self.assertDecimalEquals("300", aggs['farmer__fp__%d__MEM' % self.fp_second_payment.id].average)
        self.assertDecimalEquals("300", aggs['farmer__fp__%d__NON' % self.fp_second_payment.id].average)
        self.assertFalse('farmer__fp__%d__ALL' % self.fp_second_payment.id in aggs)

    def test_two_identical_reports(self):
        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("1"))

        SeasonAggregate.calculate_for_season(self.season)

        aggs = SeasonAggregate.for_season(self.season)

        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].best)
        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].average)

        self.assertDecimalEquals("40", aggs['expense__%d' % self.expense_washing_station.id].best)
        self.assertDecimalEquals("40", aggs['expense__%d' % self.expense_washing_station.id].average)

        self.assertDecimalEquals("3.60", aggs['expense__%d' % self.expense_capex_interest.id].best)
        self.assertDecimalEquals("3.60", aggs['expense__%d' % self.expense_capex_interest.id].average)

        self.assertDecimalEquals("43.60", aggs['total_expenses'].best)
        self.assertDecimalEquals("43.60", aggs['total_expenses'].average)

        self.assertDecimalEquals("-0.6", aggs['total_forex_loss'].best)
        self.assertDecimalEquals("-0.6", aggs['total_forex_loss'].average)

    def test_none_value(self):
        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        ExpenseEntry.objects.filter(report=nasho_report, expense=self.expense_taxes).delete()

        SeasonAggregate.calculate_for_season(self.season)
        aggs = SeasonAggregate.for_season(self.season)

        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].best)
        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].average)

        self.assertDecimalEquals("0", aggs['expense__%d' % self.expense_other.id].average)
        self.assertDecimalEquals("0", aggs['expense__%d' % self.expense_other.id].best)

        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_washing_station.id].best)
        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_washing_station.id].average)

    def test_two_different_reports(self):
        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("2"))

        SeasonAggregate.calculate_for_season(self.season)

        aggs = SeasonAggregate.for_season(self.season)

        self.assertDecimalEquals("20", aggs['expense__%d' % self.expense_cherry_advance.id].best)
        self.assertDecimalEquals("30", aggs['expense__%d' % self.expense_cherry_advance.id].average)

        self.assertDecimalEquals("40", aggs['expense__%d' % self.expense_washing_station.id].best)
        self.assertDecimalEquals("60", aggs['expense__%d' % self.expense_washing_station.id].average)

        self.assertDecimalEquals("3.60", aggs['expense__%d' % self.expense_capex_interest.id].best)
        self.assertDecimalEquals("5.40", aggs['expense__%d' % self.expense_capex_interest.id].average)

        self.assertDecimalEquals("43.60", aggs['total_expenses'].best)
        self.assertDecimalEquals("65.4", aggs['total_expenses'].average)

        self.assertDecimalEquals("-1.20", aggs['total_forex_loss'].best)
        self.assertDecimalEquals("-0.90", aggs['total_forex_loss'].average)

        self.assertDecimalEquals("30", aggs['cashuse__%d' % self.cu_second_payment.id].best)
        self.assertDecimalEquals("22.50", aggs['cashuse__%d' % self.cu_second_payment.id].average)

        self.assertDecimalEquals("450", aggs['farmer__fp__%d__MEM' % self.fp_second_payment.id].average)
        self.assertDecimalEquals("600", aggs['farmer__fp__%d__MEM' % self.fp_second_payment.id].best)

        self.assertDecimalEquals("450", aggs['farmer__fp__%d__NON' % self.fp_second_payment.id].average)
        self.assertFalse('farmer__fp__%d__ALL' % self.fp_second_payment.id in aggs)

        # check that we have report values for each wetmill
        self.assertDecimalEquals("21.80", ReportValue.objects.get(report=nasho_report, metric__slug='total_expenses__kgc').value)
        self.assertDecimalEquals("43.60", ReportValue.objects.get(report=coko_report, metric__slug='total_expenses__kgc').value)
        self.assertEquals(1, ReportValue.objects.get(report=nasho_report, metric__slug='total_expenses').rank())
        self.assertEquals(2, ReportValue.objects.get(report=coko_report, metric__slug='total_expenses').rank())

        self.assertDecimalEquals("-21500", ReportValue.objects.get(report=nasho_report, metric__slug='total_profit').value)
        self.assertDecimalEquals("-43000", ReportValue.objects.get(report=coko_report, metric__slug='total_profit').value)
        self.assertEquals(1, ReportValue.objects.get(report=nasho_report, metric__slug='total_profit').rank())
        self.assertEquals(2, ReportValue.objects.get(report=coko_report, metric__slug='total_profit').rank())

        # reload our season
        season = Season.objects.get(pk=self.season.pk)

        # check that our guage limits have been set
        self.assertDecimalEquals(season.farmer_payment_left, aggs['farmer_payment'].lowest)
        self.assertDecimalEquals(season.farmer_payment_right, aggs['farmer_payment'].highest)

        self.assertDecimalEquals(season.cherry_ratio_left, aggs['cherry_to_green_ratio'].highest)
        self.assertDecimalEquals(season.cherry_ratio_right, aggs['cherry_to_green_ratio'].lowest)

        self.assertDecimalEquals(season.total_costs_left, aggs['production_cost'].highest)
        self.assertDecimalEquals(season.total_costs_right, aggs['production_cost'].lowest)

        self.assertDecimalEquals(season.sale_price_left, aggs['fot_price'].lowest)
        self.assertDecimalEquals(season.sale_price_right, aggs['fot_price'].highest)

    test_two_different_reports.active = True



        

