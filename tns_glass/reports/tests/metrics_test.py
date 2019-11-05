from tns_glass.reports.pdf.render import PDFReport
from .base import PDFTestCase
from decimal import Decimal

class MetricsTest(PDFTestCase):

    def setUp(self):
        super(MetricsTest, self).setUp()
        self.currency = self.usd

        self.add_grades()
        self.add_productions()

        # fill out all productions so we can be finalized
        self.add_production(self.green12, Decimal("0"))
        self.add_production(self.hpc, Decimal("0"))
        self.add_production(self.triage, Decimal("0"))

        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

    def test_calculate_metrics(self):
        # no metrics before being finalized
        self.assertIsNone(self.report.farmer_price)

        # finalize our report
        self.report.finalize()

        # we should have metrics calculated
        self.assertDecimalEquals("1060.16", self.report.farmer_price)
        self.assertDecimalEquals("52", self.report.farmer_share)
        self.assertDecimalEquals("874.58", self.report.production_cost)
        self.assertDecimalEquals("6.22", self.report.cherry_to_green_ratio)

        # check conversion to USD
        self.assertDecimalEquals("1.50", self.report.production_cost_usd())
        self.report.production_cost = None
        self.assertIsNone(self.report.production_cost_usd())

        self.assertDecimalEquals("1.81", self.report.farmer_price_usd())
        self.report.farmer_price = None
        self.assertIsNone(self.report.farmer_price_usd())

