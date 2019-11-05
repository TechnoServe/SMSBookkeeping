from .base import PDFTestCase
from reports.pdf.production import ProductionBox
from reports.pdf.sales import SalesBox
from reports.pdf.expenses import ExpenseBox
from reports.pdf.cash import CashBox
from decimal import Decimal

class CashTestCase(PDFTestCase):

    def setUp(self):
        super(CashTestCase, self).setUp()

        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.save()

    def test_cash_box(self):
        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)

        self.report.miscellaneous_sources = Decimal("1")
        self.report.save()

        cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        ex = self.rwanda_2010.exchange_rate

        sources = cash.get_sources()
        self.assertEquals(3, len(sources))

        self.assertEquals("Cash Due from CSP", sources[0].name)
        self.assertDecimalEquals("8241.35", sources[0].total.as_usd(ex))

        self.assertEquals("Unused Working Capital with Cooperative", sources[1].name)
        self.assertDecimalEquals("29.23", sources[1].total.as_usd(ex))

        self.assertEquals("Miscellaneous Sources", sources[2].name)
        self.assertDecimalEquals("0", sources[2].total.as_usd(ex))

        uses = cash.get_uses()
        self.assertEquals(3, len(uses))

        self.assertEquals("Dividend", uses[0].name)
        self.assertDecimalEquals("2612", uses[0].total.as_usd(ex))

        self.assertEquals("Second Payment", uses[1].name)
        self.assertDecimalEquals("3000", uses[1].total.as_usd(ex))

        self.assertEquals("Retained Profit", uses[2].name)
        self.assertDecimalEquals("2658.59", uses[2].total.as_usd(ex))

    test_cash_box.active = True

    def test_negative_profit(self):
        # remove our first three sales
        for sale in self.report.sales.all()[:3]:
            sale.delete()

        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)

        self.report.miscellaneous_sources = Decimal("1")
        self.report.save()

        cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        ex = self.rwanda_2010.exchange_rate
        self.assertDecimalEquals("0", cash.retained_profit.as_usd(ex))


class EthiopiaCashTestCase(PDFTestCase):

    def setUp(self):
        super(EthiopiaCashTestCase, self).setUp()
        
        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
        self.add_ethiopia_expenses()
        self.add_cash_sources()
        self.add_ethiopia_cash_uses()
        self.add_ethiopia_payments()

    def test_cash_box(self):
        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.usd)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.usd)

        self.report.cash_sources.filter(cash_source=self.cs_misc_sources).delete()
        self.report.cash_sources.create(cash_source=self.cs_misc_sources, value=Decimal("1"),
                                        created_by=self.admin, modified_by=self.admin)

        cash = CashBox(self.report, self.production, self.sales, self.expenses, self.usd)

        ex = self.ethiopia_2009.exchange_rate

        sources = cash.get_sources()
        self.assertEquals(3, len(sources))

        self.assertEquals("Cash Due from CSP", sources[0].name)
        self.assertDecimalEquals("3487.44", sources[0].total.as_usd(ex))

        self.assertEquals("Unused Working Capital with Cooperative", sources[1].name)
        self.assertDecimalEquals("79.25", sources[1].total.as_usd(ex))

        self.assertEquals("Miscellaneous Sources", sources[2].name)
        self.assertDecimalEquals("0.06", sources[2].total.as_usd(ex))

        uses = cash.get_uses()
        self.assertEquals(1, len(uses))
        self.assertEquals("Dividend", uses[0].name)
        self.assertDecimalEquals("2952.00", uses[0].total.as_usd(ex))

        self.assertDecimalEquals("614.69", cash.retained_profit.as_usd(ex))


