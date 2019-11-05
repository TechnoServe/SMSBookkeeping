from django.test import TestCase
from tns_glass.tests import TNSTestCase
from .models import *
from seasons.models import *
from reports.models import *
from django.conf import settings
from django.core.urlresolvers import reverse
import os

class ImportTest(TNSTestCase):

    def setUp(self):
        super(ImportTest, self).setUp()
        self.row = 0

        season = self.rwanda_2010

        # add our grades
        self.add_grades()
        season.add_grade(self.cherry)
        season.add_grade(self.parchment)
        season.add_grade(self.green)
        season.add_grade(self.green15)
        season.add_grade(self.green13)
        season.add_grade(self.low)

        # and expenses
        self.add_expenses()
        season.add_expense(self.expense_washing_station)
        season.add_expense(self.expense_cherry_advance)
        season.add_expense(self.add_expense(self.expense_washing_station, "Labour (Full Time)"))
        season.add_expense(self.add_expense(self.expense_washing_station, "Labour (Casual)"))
        season.add_expense(self.expense_other)
        self.expense_other.order = 5
        self.expense_other.save()
        season.add_expense(self.add_expense(self.expense_other, "Batteries and Lighting"))

        milling = self.add_expense(None, "Milling, Marketing and Export Expenses")
        season.add_expense(milling)
        season.add_expense(self.add_expense(milling, "Marketing Fee"))

        working_cap = self.add_expense(None, "Working Capital Expenses")
        season.add_expense(working_cap)

        interest = self.add_expense(working_cap, "Working Capital Interest")
        interest.in_dollars = True
        interest.save()
        season.add_expense(interest)

        fee = self.add_expense(working_cap, "Working Capital Fee")
        fee.in_dollars = True
        fee.save()
        season.add_expense(fee)

        self.season = season

        # and cash uses
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.cs_misc_sources = CashSource.objects.create(name="Miscellaneous Sources Of Cash", order=2,
                                                         created_by=self.admin, modified_by=self.admin)
        self.season.cash_sources.add(self.cs_misc_sources)

        self.season.cash_uses.add(self.cu_dividend)
        self.season.cash_uses.add(self.cu_second_payment)

        self.season.farmer_payments.create(farmer_payment=self.fp_second_payment, applies_to='BOT')
        self.season.farmer_payments.create(farmer_payment=self.fp_dividend, applies_to='MEM')

    def test_views(self):
        response = self.client.get(reverse('reportimports.reportimport_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        # get a template for our season
        response = self.client.post(reverse('reportimports.reportimport_action'),
                                    dict(template='template', season=self.season.id))
        self.assertEquals(200, response.status_code)
        self.assertTrue(response.content.find("Name [name],") == 0)

        # create a new import
        response = self.client.post(reverse('reportimports.reportimport_action'), dict(create='create', season=self.season.id))
        self.assertRedirect(response, reverse('reportimports.reportimport_create'))

        create_url = response.get('Location', None)
        response = self.client.get(create_url)

        # should have a link to get our template
        self.assertContains(response, reverse('reportimports.reportimport_action'))

        # and mention our season
        self.assertContains(response, str(self.season))

        f = open(self.build_import_path("report_import_1.csv"))
        post_data = dict(csv_file=f)
        response = self.assertPost(create_url, post_data)

        # make sure a new import was created
        report_import = ReportImport.objects.get()
        self.assertEquals('PENDING', report_import.get_status())
        self.assertEquals(self.season, report_import.season)

        # while the report is pending the read page should refresh
        self.assertEquals(2000, response.context['refresh'])

        report_import.import_log = ""
        report_import.save()
        report_import.log("hello world")
        self.assertEquals("hello world\n", report_import.import_log)

        # check out our list page
        response = self.client.get(reverse('reportimports.reportimport_list'))
        self.assertEquals(1, len(response.context['object_list']))
        self.assertContains(response, str(self.season))

    def assertNextRow(self, value):
        self.assertEquals(value, self.csv[self.row][0])
        self.row += 1

    def print_csv(self):
        for row in self.csv:
            print row[0]

    def assertAttributes(self):
        # should have three columns
        self.assertEquals(3, len(self.csv[0]))

        # test our fields
        self.assertNextRow("Name [name]")
        self.assertNextRow("CSP [csp]")
        self.assertNextRow("Number of Farmers [farmers]")
        self.assertNextRow("Capacity (KG) [capacity]")

    def assertProduction(self):
        self.assertNextRow("")
        self.assertNextRow("Production")
        self.assertNextRow("Cherry - Members (KG) [cherry_mem]")
        self.assertNextRow("Cherry (KG) [prod]")
        self.assertNextRow("Parchment (KG) [prod]")
        self.assertNextRow("Green [prod]")
        self.assertNextRow("    Green - Screen 15+ (KG)")
        self.assertNextRow("    Green - Screen 13,14 (KG)")
        self.assertNextRow("    Green - Low Grades (KG)")

    def assertSales(self):
        self.assertNextRow("")
        self.assertNextRow("Sales (KG) [sales_kg]")
        for i in range(20):
            self.assertNextRow("Buyer %d" % (i+1))

        self.assertNextRow("")
        self.assertNextRow("Sales Revenue (RWF or USD) [sales_rev]")
        for i in range(20):
            self.assertNextRow("Buyer %d" % (i+1))

        self.assertNextRow("")
        self.assertNextRow("Sales Exchange Rate (RWF) [sales_exc]")
        for i in range(20):
            self.assertNextRow("Buyer %d" % (i+1))

        self.assertNextRow("")
        self.assertNextRow("Sales Type (FOB or FOT) [sales_type]")
        for i in range(20):
            self.assertNextRow("Buyer %d" % (i+1))

        self.assertNextRow("")
        self.assertNextRow("Sales Adjustment (USD) [sales_adj]")
        for i in range(20):
            self.assertNextRow("Buyer %d" % (i+1))

        self.assertNextRow("")

    def assertExpenses(self):
        self.assertNextRow("")
        self.assertNextRow("Washing Station Expenses [exp]")
        self.assertNextRow("    Cherry Advance (RWF)")
        self.assertNextRow("    Labour (Full Time) (RWF)")
        self.assertNextRow("    Labour (Casual) (RWF)")
        self.assertNextRow("    Other Expenses")
        self.assertNextRow("        Batteries and Lighting (RWF)")

        self.assertNextRow("")
        self.assertNextRow("Milling, Marketing and Export Expenses [exp]")
        self.assertNextRow("    Marketing Fee (RWF)")

        self.assertNextRow("")
        self.assertNextRow("Working Capital Expenses [exp]")
        self.assertNextRow("    Working Capital Interest (USD)")
        self.assertNextRow("    Working Capital Interest (Exchange RWF)")
        self.assertNextRow("    Working Capital Fee (USD)")
        self.assertNextRow("    Working Capital Fee (Exchange RWF)")

    def test_template(self):
        self.csv = build_sample_rows(self.rwanda_2010)

        self.assertAttributes()
        self.assertProduction()
        self.assertSales()

        self.assertNextRow("Working Capital (RWF) [working_cap]")
        self.assertNextRow("Working Capital Repaid (RWF) [working_cap_repaid]")

        self.assertExpenses()

        self.assertNextRow("")
        self.assertNextRow("Miscellaneous Sources Of Cash (RWF) [cash_source]")

        self.assertNextRow("")
        self.assertNextRow("Dividend (RWF) [cash_use]")
        self.assertNextRow("Second Payment (RWF) [cash_use]")

        self.assertNextRow("")
        self.assertNextRow("Dividend [farmer_payment]")
        self.assertNextRow("    Members (RWF/KG Cherry)")

        self.assertNextRow("")
        self.assertNextRow("Second Payment [farmer_payment]")
        self.assertNextRow("    Members (RWF/KG Cherry)")
        self.assertNextRow("    Non-Members (RWF/KG Cherry)")

        tmp_file = open('/tmp/template.csv', 'w')
        tmp_file.write(rows_to_csv(self.csv))
        tmp_file.close()

    def test_lookups(self):
        try:
            get_cash_source(self.season, "No Such Source")
            self.fail("Should have failed due to lookup")
        except:
            pass

        self.season.cash_sources.clear()
        try:
            get_cash_source(self.season, self.unused_working_cap.name)
            self.fail("Should have failed due to cash source not being present in season")
        except:
            pass

        try:
            get_farmer_payment(self.season, "No Such Payment")
            self.fail("Should have failed due to farmer payment")
        except:
            pass

        self.season.farmer_payments.all().delete()
        try:
            get_farmer_payment(self.season, self.fp_second_payment.name)
            self.fail("Should have failed due to farmer payment not being present in season")
        except:
            pass

    def test_template2(self):
        self.rwanda_2010.has_misc_revenue = True
        self.rwanda_2010.save()

        self.season.farmer_payments.get(farmer_payment=self.fp_second_payment).delete()
        self.season.farmer_payments.create(farmer_payment=self.fp_second_payment, applies_to='ALL')

        self.csv = build_sample_rows(self.rwanda_2010)

        self.assertAttributes()
        self.assertProduction()
        self.assertSales()

        self.assertNextRow("Working Capital (RWF) [working_cap]")
        self.assertNextRow("Working Capital Repaid (RWF) [working_cap_repaid]")
        self.assertNextRow("Miscellaneous Revenue (RWF) [misc_revenue]")

        self.assertExpenses()

        self.assertNextRow("")
        self.assertNextRow("Miscellaneous Sources Of Cash (RWF) [cash_source]")

        self.assertNextRow("")
        self.assertNextRow("Dividend (RWF) [cash_use]")
        self.assertNextRow("Second Payment (RWF) [cash_use]")

        self.assertNextRow("")
        self.assertNextRow("Dividend [farmer_payment]")
        self.assertNextRow("    Members (RWF/KG Cherry)")

        self.assertNextRow("")
        self.assertNextRow("Second Payment [farmer_payment]")
        self.assertNextRow("    Per Kilo (RWF/KG Cherry)")

    def test_to_csv(self):
        rows = (("one,", "two", "three"),
                ("four\"asdf", "five", "six"))

        csv = rows_to_csv(rows)

        self.assertEquals('"one,",two,three\r\n"four""asdf",five,six\r\n', csv)

    def test_import(self):
        path = self.build_import_path("report_import_1.csv")
        reports = import_season(self.season, path, self.admin)

        self.assertEquals(2, len(reports))
        self.assertEquals(self.nasho, reports[0].wetmill)
        self.assertEquals(self.coko, reports[1].wetmill)

        reports = Report.objects.filter(season=self.season)
        self.assertEquals(2, len(reports))

        report = Report.objects.get(wetmill=self.nasho, season=self.season)

        self.assertEquals(self.rtc, self.nasho.get_csp_for_season(self.season))
        self.assertDecimalEquals("10000", report.capacity)
        self.assertDecimalEquals("100", report.cherry_production_by_members)

        production = report.production_for_season_grades()
        self.assertEquals(self.cherry, production[0]['grade'])
        self.assertDecimalEquals("101", production[0]['volume'])

        self.assertEquals(self.parchment, production[1]['grade'])
        self.assertDecimalEquals("102", production[1]['volume'])

        self.assertEquals(self.green, production[2]['grade'])
        self.assertIsNone(production[2]['volume'])

        self.assertEquals(self.green15, production[3]['grade'])
        self.assertDecimalEquals("103", production[3]['volume'])

        self.assertEquals(self.green13, production[4]['grade'])
        self.assertDecimalEquals("104", production[4]['volume'])

        self.assertEquals(self.low, production[5]['grade'])
        self.assertDecimalEquals("105", production[5]['volume'])

        # test our sales
        sales = report.sales.all()
        self.assertEquals(2, len(sales))

        self.assertEquals("Rogers Family Co.", sales[0].buyer)
        self.assertEquals('FOT', sales[0].sale_type)
        self.assertDecimalEquals("0.16", sales[0].adjustment)
        self.assertDecimalEquals("591.10", sales[0].exchange_rate)
        self.assertEquals(self.usd, sales[0].currency)
        self.assertDecimalEquals("3.60", sales[0].price)

        comps = sales[0].components.all()
        self.assertEquals(1, len(comps))
        self.assertEquals(self.green15, comps[0].grade)
        self.assertDecimalEquals("660", comps[0].volume)

        self.assertEquals("Rogers Family Co.", sales[1].buyer)
        self.assertEquals('FOT', sales[1].sale_type)
        self.assertDecimalEquals("0.16", sales[1].adjustment)
        self.assertDecimalEquals("588.71", sales[1].exchange_rate)
        self.assertEquals(self.usd, sales[1].currency)
        self.assertDecimalEquals("3.60", sales[1].price)

        comps = sales[1].components.all()
        self.assertEquals(1, len(comps))
        self.assertEquals(self.green15, comps[0].grade)
        self.assertDecimalEquals("8220", comps[0].volume)

        self.assertDecimalEquals("1000", report.working_capital)
        self.assertDecimalEquals("1001", report.working_capital_repaid)

        expenses = report.entries_for_season_expenses()
        self.assertEquals("Washing Station Expenses", expenses[0]['expense'].name)
        self.assertIsNone(expenses[0]['value'])
        self.assertIsNone(expenses[0]['exchange_rate'])

        self.assertEquals("Cherry Advance", expenses[1]['expense'].name)
        self.assertDecimalEquals("1003", expenses[1]['value'])
        self.assertIsNone(expenses[1]['exchange_rate'])

        self.assertEquals("Labour (Full Time)", expenses[2]['expense'].name)
        self.assertDecimalEquals("1004", expenses[2]['value'])
        self.assertIsNone(expenses[2]['exchange_rate'])

        self.assertEquals("Labour (Casual)", expenses[3]['expense'].name)
        self.assertDecimalEquals("0", expenses[3]['value'])
        self.assertIsNone(expenses[3]['exchange_rate'])

        self.assertEquals("Other Expenses", expenses[4]['expense'].name)
        self.assertIsNone(expenses[4]['value'])
        self.assertIsNone(expenses[4]['exchange_rate'])

        self.assertEquals("Batteries and Lighting", expenses[5]['expense'].name)
        self.assertDecimalEquals("1006", expenses[5]['value'])
        self.assertIsNone(expenses[5]['exchange_rate'])

        self.assertEquals("Milling, Marketing and Export Expenses", expenses[6]['expense'].name)
        self.assertIsNone(expenses[6]['value'])
        self.assertIsNone(expenses[6]['exchange_rate'])

        self.assertEquals("Marketing Fee", expenses[7]['expense'].name)
        self.assertDecimalEquals("1007", expenses[7]['value'])
        self.assertIsNone(expenses[7]['exchange_rate'])

        self.assertEquals("Working Capital Expenses", expenses[8]['expense'].name)
        self.assertIsNone(expenses[8]['value'])
        self.assertIsNone(expenses[8]['exchange_rate'])

        self.assertEquals("Working Capital Interest", expenses[9]['expense'].name)
        self.assertDecimalEquals("1008", expenses[9]['value'])
        self.assertDecimalEquals("501", expenses[9]['exchange_rate'])

        self.assertEquals("Working Capital Fee", expenses[10]['expense'].name)
        self.assertDecimalEquals("1009", expenses[10]['value'])
        self.assertDecimalEquals("502", expenses[10]['exchange_rate'])

        cashsources = report.cash_sources_for_season()
        self.assertEquals(1, len(cashsources))

        self.assertEquals("Miscellaneous Sources Of Cash", cashsources[0].name)
        self.assertDecimalEquals("0", cashsources[0].entry.value)

        cashuses = report.cash_uses_for_season()
        self.assertEquals(2, len(cashuses))

        self.assertEquals("Dividend", cashuses[0].name)
        self.assertDecimalEquals("1010", cashuses[0].entry.value)
        self.assertEquals("Second Payment", cashuses[1].name)
        self.assertDecimalEquals("1011", cashuses[1].entry.value)

        payments = report.farmer_payments_for_season()
        self.assertEquals(2, len(payments))

        self.assertEquals("Dividend", payments[0].name)
        self.assertDecimalEquals("10", payments[0].entry.member_per_kilo)
        self.assertIsNone(payments[0].entry.non_member_per_kilo)

        self.assertEquals("Second Payment", payments[1].name)
        self.assertDecimalEquals("11", payments[1].entry.member_per_kilo)
        self.assertDecimalEquals("12", payments[1].entry.non_member_per_kilo)


        ############################################
        # Second imported report
        ############################################

        report = Report.objects.get(wetmill=self.coko, season=self.season)

        self.assertEquals(self.rtc, self.nasho.get_csp_for_season(self.season))
        self.assertDecimalEquals("10001", report.capacity)
        self.assertDecimalEquals("200", report.cherry_production_by_members)

        production = report.production_for_season_grades()
        self.assertEquals(self.cherry, production[0]['grade'])
        self.assertDecimalEquals("201", production[0]['volume'])

        self.assertEquals(self.parchment, production[1]['grade'])
        self.assertDecimalEquals("202", production[1]['volume'])

        self.assertEquals(self.green, production[2]['grade'])
        self.assertIsNone(production[2]['volume'])

        self.assertEquals(self.green15, production[3]['grade'])
        self.assertDecimalEquals("203", production[3]['volume'])

        self.assertEquals(self.green13, production[4]['grade'])
        self.assertDecimalEquals("204", production[4]['volume'])

        self.assertEquals(self.low, production[5]['grade'])
        self.assertDecimalEquals("0", production[5]['volume'])

        # test our sales
        sales = report.sales.all()
        self.assertEquals(2, len(sales))

        self.assertEquals("Rogers Family Co.", sales[0].buyer)
        self.assertEquals('FOB', sales[0].sale_type)
        self.assertIsNone(sales[0].adjustment)
        self.assertIsNone(sales[0].exchange_rate)
        self.assertEquals(self.rwf, sales[0].currency)
        self.assertDecimalEquals("1597.05", sales[0].price)

        comps = sales[0].components.all()
        self.assertEquals(1, len(comps))
        self.assertEquals(self.green13, comps[0].grade)
        self.assertDecimalEquals("39", comps[0].volume)

        self.assertEquals("Rogers Family Co.", sales[1].buyer)
        self.assertEquals('FOB', sales[1].sale_type)
        self.assertIsNone(sales[1].adjustment)
        self.assertIsNone(sales[1].exchange_rate)
        self.assertEquals(self.rwf, sales[1].currency)
        self.assertDecimalEquals("900.90", sales[1].price)

        comps = sales[1].components.all()
        self.assertEquals(1, len(comps))
        self.assertEquals(self.low, comps[0].grade)
        self.assertDecimalEquals("465", comps[0].volume)

        self.assertDecimalEquals("2000", report.working_capital)
        self.assertDecimalEquals("2001", report.working_capital_repaid)

        expenses = report.entries_for_season_expenses()
        self.assertEquals("Washing Station Expenses", expenses[0]['expense'].name)
        self.assertIsNone(expenses[0]['value'])
        self.assertIsNone(expenses[0]['exchange_rate'])

        self.assertEquals("Cherry Advance", expenses[1]['expense'].name)
        self.assertDecimalEquals("2003", expenses[1]['value'])
        self.assertIsNone(expenses[1]['exchange_rate'])

        self.assertEquals("Labour (Full Time)", expenses[2]['expense'].name)
        self.assertDecimalEquals("2004", expenses[2]['value'])
        self.assertIsNone(expenses[2]['exchange_rate'])

        self.assertEquals("Labour (Casual)", expenses[3]['expense'].name)
        self.assertDecimalEquals("2005", expenses[3]['value'])
        self.assertIsNone(expenses[3]['exchange_rate'])

        self.assertEquals("Other Expenses", expenses[4]['expense'].name)
        self.assertIsNone(expenses[4]['value'])
        self.assertIsNone(expenses[4]['exchange_rate'])

        self.assertEquals("Batteries and Lighting", expenses[5]['expense'].name)
        self.assertDecimalEquals("2006", expenses[5]['value'])
        self.assertIsNone(expenses[5]['exchange_rate'])

        self.assertEquals("Milling, Marketing and Export Expenses", expenses[6]['expense'].name)
        self.assertIsNone(expenses[6]['value'])
        self.assertIsNone(expenses[6]['exchange_rate'])

        self.assertEquals("Marketing Fee", expenses[7]['expense'].name)
        self.assertDecimalEquals("2007", expenses[7]['value'])
        self.assertIsNone(expenses[7]['exchange_rate'])

        self.assertEquals("Working Capital Expenses", expenses[8]['expense'].name)
        self.assertIsNone(expenses[8]['value'])
        self.assertIsNone(expenses[8]['exchange_rate'])

        self.assertEquals("Working Capital Interest", expenses[9]['expense'].name)
        self.assertDecimalEquals("2008", expenses[9]['value'])
        self.assertDecimalEquals("501", expenses[9]['exchange_rate'])

        self.assertEquals("Working Capital Fee", expenses[10]['expense'].name)
        self.assertDecimalEquals("2009", expenses[10]['value'])
        self.assertDecimalEquals("501", expenses[10]['exchange_rate'])

        cashsources = report.cash_sources_for_season()
        self.assertEquals(1, len(cashsources))

        self.assertEquals("Miscellaneous Sources Of Cash", cashsources[0].name)
        self.assertDecimalEquals("0", cashsources[0].entry.value)

        cashuses = report.cash_uses_for_season()
        self.assertEquals(2, len(cashuses))

        self.assertEquals("Dividend", cashuses[0].name)
        self.assertDecimalEquals("2010", cashuses[0].entry.value)
        self.assertEquals("Second Payment", cashuses[1].name)
        self.assertDecimalEquals("2011", cashuses[1].entry.value)

        payments = report.farmer_payments_for_season()
        self.assertEquals(2, len(payments))

        self.assertEquals("Dividend", payments[0].name)
        self.assertDecimalEquals("10", payments[0].entry.member_per_kilo)
        self.assertIsNone(payments[0].entry.non_member_per_kilo)

        self.assertEquals("Second Payment", payments[1].name)
        self.assertDecimalEquals("11", payments[1].entry.member_per_kilo)
        self.assertDecimalEquals("12", payments[1].entry.non_member_per_kilo)

    def test_import2(self):
        path = self.build_import_path("report_import_2.csv")

        # make this season have misc revenue
        self.season.has_misc_revenue = True
        self.season.save()

        # change our dividend to apply to 'ALL'
        self.season.farmer_payments.get(farmer_payment=self.fp_dividend).delete()
        self.season.farmer_payments.create(farmer_payment=self.fp_dividend, applies_to='ALL')

        reports = import_season(self.season, path, self.admin)

        self.assertEquals(2, len(reports))
        self.assertEquals(self.nasho, reports[0].wetmill)
        self.assertEquals(self.coko, reports[1].wetmill)

        report = reports[0]

        self.assertDecimalEquals("999", report.miscellaneous_revenue)

        cashuses = report.cash_uses_for_season()
        self.assertEquals(2, len(cashuses))

        self.assertEquals("Dividend", cashuses[0].name)
        self.assertDecimalEquals("1010", cashuses[0].entry.value)

        payments = report.farmer_payments_for_season()
        self.assertEquals(2, len(payments))
        self.assertDecimalEquals("10", payments[0].entry.all_per_kilo)
        self.assertIsNone(payments[0].entry.member_per_kilo)
        self.assertIsNone(payments[0].entry.non_member_per_kilo)

    def assertBadImport(self, filename, error):
        path = self.build_import_path(filename)

        import StringIO
        logger = StringIO.StringIO()

        try:
            reports = import_season(self.season, path, self.admin, logger)
            self.fail("Should have thrown error")
        except Exception as e:
            self.assertTrue(e.message.find(error) == 0, "Should have found error: %s, instead found: %s" % (error, e.message))

    def test_bad_imports(self):
        self.assertBadImport("report_import_bad_buyer.csv", "Unable to parse buyer")

        self.assertBadImport("report_import_no_finalize.csv", "Unable to finalize report due to missing field values.")

        self.assertBadImport("report_import_bad_season_grade.csv", "The grade 'Ungraded' is")

        self.assertBadImport("report_import_bad_grade.csv", "Unable to find grade")

        self.assertBadImport("report_import_bad_wetmill.csv", "Unable to find wetmill")

        self.assertBadImport("report_import_bad_csp.csv", "Unable to find a CSP")

        self.assertBadImport("report_import_bad_expense.csv", "Unable to find expense with")

        self.assertBadImport("report_import_invalid_expense.csv", "Unable to find expense with")

        self.assertBadImport("report_import_bad_season_expense.csv", "The expense 'Unexplained'")

        self.assertBadImport("report_import_bad_cashuse.csv", "Unable to find cash use with name")

        self.assertBadImport("report_import_bad_sale_rev.csv",  "Invalid sale revenue row, revenue label")

        self.assertBadImport("report_import_bad_sale_exc.csv",  "Invalid sale exchange rate row, exchange rate label")

        self.assertBadImport("report_import_bad_sale_type.csv",  "Invalid sales type row, sales type label")

        self.assertBadImport("report_import_bad_sale_type_name.csv",  "Invalid sale type: '' for sale to 'Rogers Family Co.")

        self.assertBadImport("report_import_bad_sale_adj.csv",  "Invalid sales adjustment row, sales adjustment label")

        self.assertBadImport("report_import_bad_decimal.csv",  "Invalid numeric value")

        self.assertBadImport("report_import_bad_sale_fob.csv",  "Invalid sales type:")

        self.assertBadImport("report_import_bad_line.csv",  "Unknown row in CSV import")

        self.assertBadImport("report_import_parent_expense.csv",  "Invalid value '1000' for expense")

        self.assertBadImport("report_import_parent_expense2.csv",  "Invalid value '1000' for expense")

        self.assertBadImport("report_import_parent_prod.csv",  "Invalid value '100' for grade")

        self.assertBadImport("report_import_bad_revenue.csv",  "Missing revenue for sale")

        self.assertBadImport("report_import_missing_sale_type.csv",  "Invalid sale type: '' for sale")

        # add agro inputs as a cash use
        CashUse.objects.create(name="Agro Inputs", order="3",
                               created_by=self.admin, modified_by=self.admin)

        self.assertBadImport("report_import_bad_season_cashuse.csv", "The cash use 'Agro Inputs' is")
