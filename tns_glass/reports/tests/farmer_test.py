from .base import PDFTestCase
from reports.pdf.production import ProductionBox
from reports.pdf.sales import SalesBox
from reports.pdf.expenses import ExpenseBox
from reports.pdf.cash import CashBox
from reports.pdf.farmer import FarmerBox
from reports.models import *
from seasons.models import *
from decimal import Decimal

class FarmerTestCase(PDFTestCase):

    def setUp(self):
        super(FarmerTestCase, self).setUp()

        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("19500")
        self.report.save()

    def test_all_cashuse(self):
        div_payment = self.season.farmer_payments.get(farmer_payment=self.fp_dividend)
        div_payment.applies_to = 'ALL'
        div_payment.save()

        self.report.farmer_payments.filter(farmer_payment=self.fp_dividend).delete()
        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, all_per_kilo=Decimal("22.25"),
                                           created_by=self.admin, modified_by=self.admin)

        self.report.cash_uses.filter(cash_use=self.cu_dividend).delete()
        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("1528020"),
                                     created_by=self.admin, modified_by=self.admin)

        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.usd)

        rows = farmer.get_rows()
        self.assertEquals(6, len(rows))

        exchange = self.season.exchange_rate

        self.assertEquals("Advance Payment", rows[0].label)
        self.assertEquals('ALL', rows[0].row_for)
        self.assertDecimalEquals("8128839.00", rows[0].value.as_local(exchange))
        self.assertFalse(rows[0].is_total)

        self.assertEquals("Dividend", rows[1].label)
        self.assertEquals('ALL', rows[1].row_for)
        self.assertDecimalEquals("1527551.50", rows[1].value.as_local(exchange))
        self.assertFalse(rows[1].is_total)

        self.assertEquals("Second Payment", rows[2].label)
        self.assertEquals('MEM', rows[2].row_for)
        self.assertDecimalEquals("2059620", rows[2].value.as_local(exchange))
        self.assertFalse(rows[2].is_total)

        self.assertEquals("Second Payment", rows[3].label)
        self.assertEquals('NON', rows[3].row_for)
        self.assertDecimalEquals("2059620", rows[3].value.as_local(exchange))
        self.assertFalse(rows[3].is_total)

        self.assertEquals("Total Farmer Payment", rows[4].label)
        self.assertEquals('MEM', rows[4].row_for)
        self.assertDecimalEquals("11716010.50", rows[4].value.as_local(exchange))
        self.assertTrue(rows[4].is_total)

        self.assertEquals("Total Farmer Payment", rows[5].label)
        self.assertEquals('NON', rows[5].row_for)
        self.assertDecimalEquals("11716010.50", rows[5].value.as_local(exchange))
        self.assertTrue(rows[5].is_total)

        self.assertDecimalEquals("68", farmer.farmer_percentage)
        self.assertDecimalEquals("52", farmer.member_price_share)
        self.assertDecimalEquals("52", farmer.non_member_price_share)

    def test_no_entry(self):
        # remove our entry for our second payment
        self.report.farmer_payments.filter(farmer_payment=self.fp_second_payment).delete()
        self.report.cash_uses.filter(cash_use=self.cu_second_payment).delete()

        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        exchange = self.season.exchange_rate
        farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.usd)

        rows = farmer.get_rows()
        self.assertEquals(6, len(rows))

        self.assertEquals("Advance Payment", rows[0].label)
        self.assertEquals('ALL', rows[0].row_for)
        self.assertDecimalEquals("8128839.00", rows[0].value.as_local(exchange))
        self.assertFalse(rows[0].is_total)

        self.assertEquals("Dividend", rows[1].label)
        self.assertEquals('MEM', rows[1].row_for)
        self.assertDecimalEquals("1510388", rows[1].value.as_local(exchange))
        self.assertFalse(rows[1].is_total)

        self.assertEquals("Second Payment", rows[2].label)
        self.assertEquals('MEM', rows[2].row_for)
        self.assertIsNone(rows[2].value)
        self.assertFalse(rows[2].is_total)

        self.assertEquals("Second Payment", rows[3].label)
        self.assertEquals('NON', rows[3].row_for)
        self.assertIsNone(rows[3].value)
        self.assertFalse(rows[3].is_total)

        self.assertEquals("Total Farmer Payment", rows[4].label)
        self.assertEquals('MEM', rows[4].row_for)
        self.assertDecimalEquals("9639227", rows[4].value.as_local(exchange))
        self.assertTrue(rows[4].is_total)

        self.assertEquals("Total Farmer Payment", rows[5].label)
        self.assertEquals('NON', rows[5].row_for)
        self.assertDecimalEquals("8128839", rows[5].value.as_local(exchange))
        self.assertTrue(rows[5].is_total)

        self.assertDecimalEquals("32", farmer.farmer_percentage)
        self.assertDecimalEquals("43", farmer.member_price_share)
        self.assertDecimalEquals("36", farmer.non_member_price_share)

    def test_no_members(self):
        div_payment = self.season.farmer_payments.get(farmer_payment=self.fp_dividend)
        div_payment.applies_to = 'ALL'
        div_payment.save()

        exchange = self.season.exchange_rate

        # this will also remove the season entries
        self.fp_second_payment.delete()
        self.cu_second_payment.delete()

        self.report.farmer_payments.filter(farmer_payment=self.fp_dividend).delete()
        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, all_per_kilo=Decimal("22.25"),
                                           created_by=self.admin, modified_by=self.admin)

        self.report.cash_uses.filter(cash_use=self.cu_dividend).delete()
        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("1528020"),
                                     created_by=self.admin, modified_by=self.admin)

        # make our season have no members
        self.rwanda_2010.has_members = False
        self.rwanda_2010.save()

        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.usd)

        rows = farmer.get_rows()
        self.assertEquals(3, len(rows))

        self.assertEquals("Advance Payment", rows[0].label)
        self.assertEquals('ALL', rows[0].row_for)
        self.assertDecimalEquals("8128839.00", rows[0].value.as_local(exchange))
        self.assertFalse(rows[0].is_total)

        self.assertEquals("Dividend", rows[1].label)
        self.assertEquals('ALL', rows[1].row_for)
        self.assertDecimalEquals("1527551.50", rows[1].value.as_local(exchange))
        self.assertFalse(rows[1].is_total)

        self.assertEquals("Total Farmer Payment", rows[2].label)
        self.assertEquals('ALL', rows[2].row_for)
        self.assertDecimalEquals("9656390.50", rows[2].value.as_local(exchange))
        self.assertTrue(rows[2].is_total)

        self.assertDecimalEquals("32", farmer.farmer_percentage)
        self.assertIsNone(farmer.member_price_share)
        self.assertIsNone(farmer.non_member_price_share)

    def test_farmer_box(self):
        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        exchange = self.season.exchange_rate
        farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.usd)

        rows = farmer.get_rows()
        self.assertEquals(6, len(rows))

        self.assertEquals("Advance Payment", rows[0].label)
        self.assertEquals('ALL', rows[0].row_for)
        self.assertDecimalEquals("8128839.00", rows[0].value.as_local(exchange))
        self.assertFalse(rows[0].is_total)

        self.assertEquals("Dividend", rows[1].label)
        self.assertEquals('MEM', rows[1].row_for)
        self.assertDecimalEquals("1510388", rows[1].value.as_local(exchange))
        self.assertFalse(rows[1].is_total)

        self.assertEquals("Second Payment", rows[2].label)
        self.assertEquals('MEM', rows[2].row_for)
        self.assertDecimalEquals("2059620", rows[2].value.as_local(exchange))
        self.assertFalse(rows[2].is_total)

        self.assertEquals("Second Payment", rows[3].label)
        self.assertEquals('NON', rows[3].row_for)
        self.assertDecimalEquals("2059620", rows[3].value.as_local(exchange))
        self.assertFalse(rows[3].is_total)

        self.assertEquals("Total Farmer Payment", rows[4].label)
        self.assertEquals('MEM', rows[4].row_for)
        self.assertDecimalEquals("11698847", rows[4].value.as_local(exchange))
        self.assertTrue(rows[4].is_total)

        self.assertEquals("Total Farmer Payment", rows[5].label)
        self.assertEquals('NON', rows[5].row_for)
        self.assertDecimalEquals("10188459", rows[5].value.as_local(exchange))
        self.assertTrue(rows[5].is_total)

        self.assertDecimalEquals("68", farmer.farmer_percentage)
        self.assertDecimalEquals("52", farmer.member_price_share)
        self.assertDecimalEquals("45", farmer.non_member_price_share)

class EthiopiaFarmerTestCase(PDFTestCase):

    def setUp(self):
        super(EthiopiaFarmerTestCase, self).setUp()

        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
        self.add_ethiopia_expenses()
        self.add_ethiopia_cash_uses()
        self.add_ethiopia_payments()

    def test_farmer_box(self):
        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        exchange = self.season.exchange_rate
        farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.usd)

        ex = self.report.season.exchange_rate

        rows = farmer.get_rows()
        self.assertEquals(4, len(rows))

        self.assertEquals("Advance Payment", rows[0].label)
        self.assertEquals('ALL', rows[0].row_for)
        self.assertDecimalEquals("15635.95", rows[0].value.as_usd(ex))
        self.assertFalse(rows[0].is_total)

        self.assertEquals("Dividend", rows[1].label)
        self.assertEquals('MEM', rows[1].row_for)
        self.assertDecimalEquals("2449.35", rows[1].value.as_usd(ex))
        self.assertFalse(rows[1].is_total)

        self.assertEquals("Total Farmer Payment", rows[2].label)
        self.assertEquals('MEM', rows[2].row_for)
        self.assertDecimalEquals("18085.29", rows[2].value.as_usd(ex))
        self.assertTrue(rows[2].is_total)

        self.assertEquals("Total Farmer Payment", rows[3].label)
        self.assertEquals('NON', rows[3].row_for)
        self.assertDecimalEquals("15635.95", rows[3].value.as_usd(ex))
        self.assertTrue(rows[3].is_total)

        self.assertDecimalEquals("36.13", farmer.farmer_price.as_local(ex))

        self.assertDecimalEquals("83", farmer.farmer_percentage)

        self.assertDecimalEquals("57", farmer.member_price_share)
        self.assertDecimalEquals("49", farmer.non_member_price_share)



