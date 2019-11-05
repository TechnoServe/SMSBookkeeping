from django.test import TestCase
from .base import PDFTestCase
from decimal import Decimal
from reports.pdf.production import ProductionBox
from reports.pdf.sales import SalesBox
from reports.pdf.expenses import ExpenseBox

class ExpenseTest(PDFTestCase):

    def setUp(self):
        super(ExpenseTest, self).setUp()

        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()

    def test_expense_box_misc_revenue(self):
        self.season.has_misc_revenue = True
        self.season.save()

        self.report.miscellaneous_revenue = Decimal("100000")
        self.report.save()

        production_box = ProductionBox(self.report)
        sales_box = SalesBox(self.report, self.usd)
        box = ExpenseBox(self.report, production_box, sales_box, self.usd)

        ex = self.rwanda_2010.exchange_rate
        self.assertDecimalEquals("38648.05", box.total_revenue.as_usd(ex))
        self.assertDecimalEquals("38477.11", box.sales_revenue.as_usd(ex))
        self.assertDecimalEquals("170.94", box.misc_revenue.as_usd(ex))

        # also make sure it works if not set
        self.report.miscellaneous_revenue = None
        self.report.save()

        production_box = ProductionBox(self.report)
        sales_box = SalesBox(self.report, self.usd)
        box = ExpenseBox(self.report, production_box, sales_box, self.usd)

        ex = self.rwanda_2010.exchange_rate
        self.assertDecimalEquals("38477.11", box.total_revenue.as_usd(ex))
        self.assertDecimalEquals("38477.11", box.sales_revenue.as_usd(ex))
        self.assertIsNone(box.misc_revenue.as_usd(ex))

    def test_expense_box_usd(self):
        production_box = ProductionBox(self.report)
        sales_box = SalesBox(self.report, self.usd)
        box = ExpenseBox(self.report, production_box, sales_box, self.usd)

        ex = self.rwanda_2010.exchange_rate

        categories = box.get_categories()
        self.assertEquals(4, len(categories))

        wash = categories[0]
        self.assertEquals("Washing Station Expenses", wash.name)
        self.assertIn("Washing Station Expenses - 11261700", str(wash))
        rows = wash.children

        self.assertEquals("Cherry Advance", rows[0].name)
        self.assertDecimalEquals("13895.45", rows[0].value.as_usd(ex))

        self.assertEquals("Cherry Transport", rows[1].name)
        self.assertDecimalEquals("1009", rows[1].value.as_usd(ex))

        self.assertEquals("Labor (Full-Time)", rows[2].name)
        self.assertDecimalEquals("1034.19", rows[2].value.as_usd(ex))

        self.assertEquals("Labor (Casual)", rows[3].name)
        self.assertDecimalEquals("1704.10", rows[3].value.as_usd(ex))

        self.assertEquals("Other expenses", rows[4].name)
        self.assertDecimalEquals("1608.03", rows[4].value.as_usd(ex))

        self.assertDecimalEquals("19250.77", wash.value.as_usd(ex))

        self.assertDecimalEquals("5355.32", wash.non_advance_value().as_usd(ex))

        mill = categories[1]
        self.assertEquals("Milling, Marketing and Export Expenses", mill.name)
        rows = mill.children

        self.assertEquals("Marketing Fee", rows[0].name)
        self.assertDecimalEquals("2584.68", rows[0].value.as_usd(ex))

        self.assertEquals("Milling", rows[1].name)
        self.assertDecimalEquals("830.42", rows[1].value.as_usd(ex))

        self.assertEquals("Hand Sorting", rows[2].name)
        self.assertDecimalEquals("354.19", rows[2].value.as_usd(ex))

        self.assertEquals("Export Bagging", rows[3].name)
        self.assertDecimalEquals("253.75", rows[3].value.as_usd(ex))

        self.assertEquals("Transport", rows[4].name)
        self.assertDecimalEquals("100", rows[4].value.as_usd(ex))

        self.assertEquals("Storage and Handling", rows[5].name)
        self.assertDecimalEquals("43", rows[5].value.as_usd(ex))

        self.assertEquals("Government Taxes, Fees and Deductions", rows[6].name)
        self.assertDecimalEquals("1513.95", rows[6].value.as_usd(ex))

        self.assertEquals("Freight and Insurance", rows[7].name)
        self.assertDecimalEquals("1951.60", rows[7].value.as_usd(ex))

        self.assertEquals("Other", rows[8].name)
        self.assertDecimalEquals("0", rows[8].value.as_usd(ex))

        self.assertDecimalEquals("7631.58", mill.value.as_usd(ex))

        capex1 = categories[2]
        self.assertEquals("Working Capital Financing Expenses", capex1.name)
        rows = capex1.children

        self.assertEquals("Working Capital Interest", rows[0].name)
        self.assertDecimalEquals("259.51", rows[0].value.as_usd(ex))

        self.assertEquals("Working Capital Fee", rows[1].name)
        self.assertDecimalEquals("192.51", rows[1].value.as_usd(ex))

        self.assertDecimalEquals("452.02", capex1.value.as_usd(ex))

        capex2 = categories[3]
        self.assertEquals("CAPEX Financing Expenses", capex2.name)
        rows = capex2.children

        self.assertEquals("CAPEX Principal Repayment", rows[0].name)
        self.assertDecimalEquals("2440.23", rows[0].value.as_usd(ex))

        self.assertEquals("CAPEX Interest", rows[1].name)
        self.assertDecimalEquals("618.23", rows[1].value.as_usd(ex))

        self.assertDecimalEquals("3058.46", capex2.value.as_usd(ex))

        self.assertDecimalEquals("30392.83", box.total.as_usd(ex))

        self.assertDecimalEquals("-186.30", box.total_forex_loss.as_usd(ex))

        self.assertDecimalEquals("8270.59", box.total_profit.as_usd(ex))

        self.assertIsNone(box.misc_revenue.as_usd(ex))
        self.assertDecimalEquals("38477.11", box.total_revenue.as_usd(ex))
        self.assertDecimalEquals("38477.11", box.sales_revenue.as_usd(ex))

class EthiopiaExpenseTest(PDFTestCase):

    def setUp(self):
        super(EthiopiaExpenseTest, self).setUp()

        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
        self.add_ethiopia_expenses()

    def test_expense_box_usd(self):
        production_box = ProductionBox(self.report)
        sales_box = SalesBox(self.report, self.usd)
        box = ExpenseBox(self.report, production_box, sales_box, self.usd)

        ex = self.ethiopia_2009.exchange_rate

        categories = box.get_categories()
        self.assertEquals(4, len(categories))

        wash = categories[0]
        self.assertEquals("Washing Station Expenses", wash.name)
        rows = wash.children

        self.assertEquals("Cherry Advance", rows[0].name)
        self.assertDecimalEquals("15635.95", rows[0].value.as_usd(ex))
        self.assertEquals("Cherry Transport", rows[1].name)
        self.assertDecimalEquals("279.08", rows[1].value.as_usd(ex))
        self.assertEquals("Labor (Full-Time)", rows[2].name)
        self.assertDecimalEquals("326.18", rows[2].value.as_usd(ex))
        self.assertEquals("Labor (Casual)", rows[3].name)
        self.assertDecimalEquals("496.56", rows[3].value.as_usd(ex))
        self.assertEquals("Other expenses", rows[4].name)
        self.assertDecimalEquals("1297", rows[4].value.as_usd(ex))
        self.assertDecimalEquals("18034.75", wash.value.as_usd(ex))

        self.assertDecimalEquals("2398.81", wash.non_advance_value().as_usd(ex))

        mill = categories[1]
        self.assertEquals("Milling, Marketing and Export Expenses", mill.name)
        rows = mill.children

        self.assertEquals("Marketing Commission", rows[0].name)
        self.assertDecimalEquals("1570.92", rows[0].value.as_usd(ex))

        self.assertEquals("Export Costs", rows[1].name)
        self.assertDecimalEquals("365.58", rows[1].value.as_usd(ex))

        self.assertEquals("Milling Fee", rows[2].name)
        self.assertDecimalEquals("746.57", rows[2].value.as_usd(ex))

        self.assertEquals("Transport", rows[3].name)
        self.assertDecimalEquals("46.20", rows[3].value.as_usd(ex))

        self.assertDecimalEquals("2729.28", mill.value.as_usd(ex))
        self.assertDecimalEquals("2729.28", mill.non_advance_value().as_usd(ex))

        capex1 = categories[2]
        self.assertEquals("Working Capital Financing Expenses", capex1.name)
        rows = capex1.children

        self.assertEquals("Interest Expense", rows[0].name)
        self.assertDecimalEquals("1394.03", rows[0].value.as_usd(ex))

        self.assertEquals("Bank Fees", rows[1].name)
        self.assertDecimalEquals("0", rows[1].value.as_usd(ex))

        self.assertDecimalEquals("1394.03", capex1.value.as_usd(ex))
        self.assertDecimalEquals("1394.03", capex1.non_advance_value().as_usd(ex))

        capex2 = categories[3]
        self.assertEquals("CAPEX Financing Expenses", capex2.name)
        rows = capex2.children

        self.assertEquals("CAPEX Principal Repayment", rows[0].name)
        self.assertDecimalEquals("4820.59", rows[0].value.as_usd(ex))

        self.assertEquals("CAPEX Interest", rows[1].name)
        self.assertDecimalEquals("1324.16", rows[1].value.as_usd(ex))

        self.assertDecimalEquals("6144.75", capex2.value.as_usd(ex))

        self.assertDecimalEquals("28302.82", box.total.as_usd(ex))

        self.assertDecimalEquals("0", box.total_forex_loss.as_usd(ex))

        self.assertDecimalEquals("3566.69", box.total_profit.as_usd(ex))

        self.assertDecimalEquals("31869.51", box.total_revenue.as_usd(ex))
        
