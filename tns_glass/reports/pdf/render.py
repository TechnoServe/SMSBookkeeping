import os
import math
from .production import ProductionBox
from .sales import SalesBox
from .expenses import ExpenseBox
from .cash import CashBox
from .farmer import FarmerBox
from .currencyvalue import CurrencyValue as CV
from locales.models import comma_formatted, Currency, Weight
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth, getAscent, getDescent

from canvas.page import PDFPage
from reports.models import Report

from decimal import Decimal, ROUND_HALF_UP
import os

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate

class PDFReport(PDFPage):

    PROD_BOX_WIDTH = 150
    PROD_BOX_HEADER_COLS = ((80, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT),
                            (40, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                            (30, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))

    PROD_BOX_CATEGORY_COLS = ((80, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT),
                              (40, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.WEIGHT),
                              (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.EVEN))

    PROD_BOX_ROW_COLS = ((70, PDFPage.BOX_ITALIC, PDFPage.LEFT),
                         (40, PDFPage.BOX_ITALIC, PDFPage.RIGHT, PDFPage.WEIGHT),
                         (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.EVEN))

    PROD_BOX_ROW_MARGIN = 10

    RATIO_BOX_COLS = ((120, PDFPage.BOX_FONT, PDFPage.LEFT),
                      (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.DECIMAL))

    SALES_BOX_WIDTH = 0

    SALES_BOX_HEADER_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                             (30, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                             (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                             (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                             (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))

    SALES_BOX_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                      (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.WEIGHT),
                      (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                      (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                      (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN))

    SALES_BOX_FOT_COLS = ((200, PDFPage.BOX_ITALIC, PDFPage.LEFT),)

    SALES_BOX_TOTAL_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                            (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.WEIGHT),
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN))

    LOCAL_SALES_BOX_HEADER_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                                   (30, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                                   (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                                   (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))

    LOCAL_SALES_BOX_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                            (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.WEIGHT),
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN, PDFPage.PER_WEIGHT_KILO))

    LOCAL_SALES_BOX_TOTAL_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                                  (30, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.WEIGHT),
                                  (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_KILO),
                                  (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN, PDFPage.PER_WEIGHT_KILO))

    WORKING_CAPITAL_WIDTH = 0

    WORKING_CAPITAL_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                            (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN))

    EXPENSE_BOX_WIDTH = 0

    EXPENSE_BOX_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                        (50, PDFPage.BOX_FONT, PDFPage.RIGHT),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    EXPENSE_HEADER1_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                            (140, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER),
                            (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                            (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))

    EXPENSE_HEADER2_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                            (50, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                            (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                            (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT),
                            (90, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))

    EXPENSE_TOTAL_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                          (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                          (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_UNIT_GREEN),
                          (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                          (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    EXPENSE_CATEGORY_MARGIN = 10

    EXPENSE_CATEGORY_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                             (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                             (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_UNIT_GREEN),
                             (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                             (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    EXPENSE_CATEGORY_TOTAL_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT],
                                   (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_UNIT_GREEN),
                                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    EXPENSE_ROW_MARGIN = 20

    EXPENSE_ROW_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                        (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_UNIT_GREEN),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                        (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    EXPENSE_FOT_COLS = ((300, PDFPage.BOX_ITALIC, PDFPage.LEFT),)

    FARMER_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT, PDFPage.RAW, PDFPage.RAW],
                   (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.LOCAL, PDFPage.PER_WEIGHT_UNIT_CHERRY),
                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_GREEN_RATIO),
                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                   (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    FARMER_TOTAL_COLS = ([60, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT, PDFPage.RAW, PDFPage.RAW],
                         (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.LOCAL, PDFPage.PER_WEIGHT_UNIT_CHERRY),
                         (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_GREEN_RATIO),
                         (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                         (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    CASH_COLS = ([60, PDFPage.BOX_FONT, PDFPage.LEFT],
                 (50, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                 (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR, PDFPage.PER_WEIGHT_UNIT_CHERRY),
                 (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_AVERAGE),
                 (90, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_CONVERT, PDFPage.AGGREGATE_BEST))

    FARMER_SUMMARY_COLS = ([100, PDFPage.BOX_FONT, PDFPage.CENTER],)

    GAUGE_MARGIN = 5
    GAUGE_DIAL = os.path.join(settings.RESOURCES_DIR, 'gauge_dial.png')
    GAUGE_DIAL_CAP = os.path.join(settings.RESOURCES_DIR, 'gauge_dial_cap.png')
    GAUGE_BG = os.path.join(settings.RESOURCES_DIR, 'gauge_background.png')

    FARMER_PAYMENT_BOX_WIDTH = 290
    FARMER_PAYMENT_BOX_HEADER_COLS = ((60, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN),
                                      [170, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER],
                                      (60, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN))

    HISTORICAL_SECTION_BOX_WIDTH = 0
    HISTORICAL_SECTION_BOX_HEADER_COLS = ([140, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT, PDFPage.RAW],
                                          (80, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.RAW),
                                          (80, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.RAW),
                                          (80, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.RAW))

    HISTORICAL_SECTION_BOX_COLS = ([140, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT, PDFPage.RAW],
                                          (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.RAW),
                                          (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.RAW),
                                          (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.RAW))

    HISTORICAL_SECTION_BOX_COLS_CUR = ([140, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT, PDFPage.RAW],
                                       (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                                       (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN),
                                       (80, PDFPage.BOX_FONT, PDFPage.RIGHT, PDFPage.CURR_EVEN))

    HISTORICAL_SECTION_BOX_COLS_HDR = ([140, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT, PDFPage.RAW],
                                       (80, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT, PDFPage.RAW),
                                       (80, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT, PDFPage.RAW),
                                       (80, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT, PDFPage.RAW))


    PERFORMANCE_BOX_HEADER_WIDTH = 585

    PERFORMANCE_BOX_HEADER_COLS = ((250, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN),
                                   (250, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN),
                                   (85, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN))

    BARGRAPH_BOX_HEADER_WIDTH = 192

    BARGRAPH_BOX_HEADER_COLS = ((96, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN),
                                (96, PDFPage.BOX_FONT_BOLD, PDFPage.CENTER, PDFPage.CURR_EVEN))

    RWANDA_MAP = os.path.join(settings.RESOURCES_DIR, 'rwanda.png')
    KENYA_MAP = os.path.join(settings.RESOURCES_DIR, 'kenya.png')
    ETHIOPIA_MAP = os.path.join(settings.RESOURCES_DIR, 'ethiopia.png')
    TANZANIA_MAP = os.path.join(settings.RESOURCES_DIR, 'tanzania.png')

    TNS_LOGO = os.path.join(settings.RESOURCES_DIR, 'tns_report_logo.png')

    # raw image is 194x36, aspect ratio should be maintained with whatever we set here
    TNS_LOGO_HEIGHT = 14
    TNS_LOGO_WIDTH = 75

    def __init__(self, report, currency, weight, report_mode, show_graphs=True, show_buyers=True):
        self.report = report
        self.season = self.report.season
        self.report_currency = currency
        self.curr_abbreviation = currency.abbreviation
        self.local_currency = self.report.wetmill.country.currency
        self.local_abbreviation = self.local_currency.abbreviation
        self.usd = Currency.objects.get(currency_code='USD')
        self.exchange = self.report.season.exchange_rate

        self.report_weight = weight
        self.weight_abbreviation = weight.abbreviation.upper()
        self.local_weight = self.report.wetmill.country.weight
        self.kilos = Weight.objects.get(abbreviation__iexact="Kg")
        self.weight_ratio = weight.ratio_to_kilogram

        self.production = ProductionBox(self.report)
        self.sales = SalesBox(self.report, self.report_currency)
        self.expenses = ExpenseBox(self.report, self.production, self.sales, self.report_currency)
        self.cash = CashBox(self.report, self.production, self.sales, self.expenses, self.report_currency)
        self.farmer = FarmerBox(self.report, self.production, self.sales, self.expenses, self.cash, self.report_currency)

        # get the aggregates for this season
        from aggregates.models import SeasonAggregate
        self.aggs = SeasonAggregate.for_season(self.report.season)

        self.show_graphs = show_graphs
        self.show_buyers = show_buyers

        # Are we showing Credit Report or Transparency Report
        self.report_mode = report_mode

        self.calculate_metrics()
        
    def calculate_metrics(self):
        self.HEADER_ASCENT = getAscent(self.HEADER_FONT, self.HEADER_SIZE)
        self.HEADER_DESCENT = -getDescent(self.HEADER_FONT, self.HEADER_SIZE)
        self.HEADER_HEIGHT = self.HEADER_ASCENT + self.HEADER_DESCENT + self.HEADER_PADDING * 2

        self.BOX_ASCENT = getAscent(self.BOX_FONT, self.BOX_SIZE)
        self.BOX_DESCENT = -getDescent(self.BOX_FONT, self.BOX_SIZE)
        self.BOX_HEIGHT = self.BOX_ASCENT + self.BOX_DESCENT + self.BOX_PADDING * 2

        self.NO_DIGITS = Decimal("1")
        self.TWO_DIGITS = Decimal(".01")

        self.HISTORICAL_SECTION_BOX_WIDTH = self.WIDTH - self.PAGE_MARGIN * 2 - self.SECTION_MARGIN
        self.HISTORICAL_SECTION_BOX_HEADER_COLS[0][0] = self.HISTORICAL_SECTION_BOX_WIDTH - 3 * self.HISTORICAL_SECTION_BOX_HEADER_COLS[2][0] - self.HISTORICAL_SECTION_BOX_HEADER_COLS[1][0]
        self.HISTORICAL_SECTION_BOX_COLS[0][0] = self.HISTORICAL_SECTION_BOX_HEADER_COLS[0][0]
        self.HISTORICAL_SECTION_BOX_COLS_HDR[0][0] = self.HISTORICAL_SECTION_BOX_COLS[0][0]
        self.HISTORICAL_SECTION_BOX_COLS_CUR[0][0] = self.HISTORICAL_SECTION_BOX_COLS[0][0]

        self.SALES_BOX_WIDTH = self.WIDTH - self.PAGE_MARGIN * 2 - self.PROD_BOX_WIDTH - self.SECTION_MARGIN
        self.SALES_BOX_HEADER_COLS[0][0]= self.SALES_BOX_WIDTH - 3 * self.SALES_BOX_HEADER_COLS[2][0] - self.SALES_BOX_HEADER_COLS[1][0]
        self.SALES_BOX_COLS[0][0]= self.SALES_BOX_HEADER_COLS[0][0]
        self.SALES_BOX_TOTAL_COLS[0][0]= self.SALES_BOX_HEADER_COLS[0][0]

        self.LOCAL_SALES_BOX_HEADER_COLS[0][0] = self.SALES_BOX_WIDTH - 2 * self.LOCAL_SALES_BOX_HEADER_COLS[2][0]- self.SALES_BOX_HEADER_COLS[1][0]
        self.LOCAL_SALES_BOX_COLS[0][0]= self.LOCAL_SALES_BOX_HEADER_COLS[0][0]
        self.LOCAL_SALES_BOX_TOTAL_COLS[0][0]= self.LOCAL_SALES_BOX_HEADER_COLS[0][0]

        self.WORKING_CAPITAL_WIDTH = self.SALES_BOX_WIDTH
        self.WORKING_CAPITAL_COLS[0][0] = self.WORKING_CAPITAL_WIDTH - self.WORKING_CAPITAL_COLS[1][0]

        self.EXPENSE_BOX_WIDTH = self.WIDTH - 2 * self.PAGE_MARGIN
        self.EXPENSE_BOX_COLS[0][0] = self.EXPENSE_BOX_WIDTH - 3 * self.EXPENSE_BOX_COLS[2][0] - self.EXPENSE_BOX_COLS[1][0]
        self.EXPENSE_HEADER1_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0]
        self.EXPENSE_HEADER2_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0]

        self.EXPENSE_TOTAL_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0]
        self.EXPENSE_CATEGORY_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0] - self.EXPENSE_CATEGORY_MARGIN
        self.EXPENSE_CATEGORY_TOTAL_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0] - self.EXPENSE_ROW_MARGIN
        self.EXPENSE_ROW_COLS[0][0] = self.EXPENSE_BOX_COLS[0][0] - self.EXPENSE_ROW_MARGIN

        self.CASH_COLS[0][0] = self.EXPENSE_CATEGORY_COLS[0][0]

        self.FARMER_COLS[0][0] = self.EXPENSE_TOTAL_COLS[0][0]
        self.FARMER_TOTAL_COLS[0][0] = self.EXPENSE_TOTAL_COLS[0][0]

        self.FARMER_SUMMARY_COLS[0][0] = self.WIDTH - 2 * self.PAGE_MARGIN

    def decimal_to_string(self, n, force_even=False):
        """Converts a number to a nicely formatted string.
        Example: 6874 => '6,874'."""
        if n is None:  # pragma: no cover
            return ""

        if isinstance(n, str) or isinstance(n, unicode):
            return n

        if force_even:
            n = n.quantize(self.NO_DIGITS, ROUND_HALF_UP)
        else:
            n = n.quantize(self.TWO_DIGITS, ROUND_HALF_UP)

        # round it appropriately
        return comma_formatted(n, not force_even)

    def per_weight_unit(self, value, kilos):
        if value is None or not kilos:
            return None

        return value * self.weight_ratio / kilos

    def per_weight_unit_cherry(self, value):
        return self.per_weight_unit(value, self.production.cherry_total)

    def per_weight_unit_green(self, value):
        return self.per_weight_unit(value, self.production.green_total)

    def per_green_ratio(self, value):
        per_weight_unit_cherry = self.per_weight_unit_cherry(value)

        # multiply by our final ratio
        if not per_weight_unit_cherry is None:
            return per_weight_unit_cherry * self.production.cherry_to_green_ratio
        else:
            return None

    def transform_value(self, value, transformation):
        if transformation == self.PER_WEIGHT_UNIT_CHERRY:
            return self.per_weight_unit_cherry(value)
        elif transformation == self.PER_WEIGHT_UNIT_GREEN:
            return self.per_weight_unit_green(value)
        elif transformation == self.PER_GREEN_RATIO:
            return self.per_green_ratio(value)
        elif transformation == self.PER_WEIGHT_KILO:
            return self.per_weight_unit(value, Decimal('1'))
        elif transformation == self.AGGREGATE_BEST:
            if value in self.aggs and self.aggs[value].best is not None:
                return self.aggs[value].best * self.weight_ratio
            else:
                return None
        elif transformation == self.AGGREGATE_AVERAGE:
            if value in self.aggs and self.aggs[value].average is not None:
                return self.aggs[value].average * self.weight_ratio
            else:
                return None
        else:
            return value

    def draw_production_boxes(self, c, y):
        width = self.PROD_BOX_WIDTH
        orig_y = y
        top_y = y

        x = self.PAGE_MARGIN
        y += self.draw_box_header(c, x, y, _("Production"), self.PROD_BOX_HEADER_COLS, (_("Type"), _("%s") % self.weight_abbreviation, "%"))

        for category in self.production.get_categories():
            y += self.draw_row(c, x, y, self.PROD_BOX_CATEGORY_COLS, (category.name, category.volume, None))

            # only draw subrows for green grades
            if category.rows and category.grade.kind == 'GRE':
                for row in category.rows:
                    y += self.draw_row(c, x+self.PROD_BOX_ROW_MARGIN, y, self.PROD_BOX_ROW_COLS, 
                                       (row.name, row.volume, self.decimal_to_string(row.percent, True) + "%"))

            y += self.BOX_PADDING
        
        y -= self.BOX_PADDING
        c.rect(x, top_y, width, y - top_y)

        y += self.SECTION_MARGIN
        top_y = y

        header_text = _("Production Ratios")
        if self.report.season.has_unprocessed_grades():
            header_text = _("Washed Coffee Production Ratios")

        y += self.draw_box_header(c, x, y, header_text, self.RATIO_BOX_COLS, None)
        y += self.draw_row(c, x, y, self.RATIO_BOX_COLS, 
                           (_("Cherry to Parchment"), self.production.cherry_to_parchment_ratio))
        y += self.draw_row(c, x, y, self.RATIO_BOX_COLS, 
                           (_("Parchment to Green"), self.production.parchment_to_green_ratio))
        y += self.draw_row(c, x, y, self.RATIO_BOX_COLS, 
                           (_("Cherry to Green"), self.production.cherry_to_green_ratio))
        
        c.rect(x, top_y, width, y - top_y)

        return y - orig_y

    def draw_sales_box(self, c, y):
        x = self.PAGE_MARGIN + self.PROD_BOX_WIDTH + self.SECTION_MARGIN
        top_y = y

        y += self.draw_box_header(c, x, y, _("Green Coffee Sales (FOT Actual and FOB Equivalent)"),
                                  self.SALES_BOX_HEADER_COLS,
                                  (_("Buyer"), _("%s") % self.weight_abbreviation, _("%s/%s (FOT or Equiv)") % (self.curr_abbreviation, self.weight_abbreviation),
                                   _("%s/%s (FOB or Equiv)") % (self.curr_abbreviation, self.weight_abbreviation), _("FOB Revenue %s") % self.curr_abbreviation))

        export_rows = self.sales.get_export_rows()
        if len(export_rows) > 1:
            for (i, sale) in enumerate(export_rows[:-1]):
                if not self.show_buyers:
                    buyer = "Buyer %d" % (i+1)
                else:
                    buyer = None

                y += self.draw_row(c, x, y, self.SALES_BOX_COLS,
                                   (sale.get_buyer_display(buyer), sale.volume, sale.fot_price, sale.fob_price, sale.revenue))
            
        y += self.PAGE_MARGIN

        y += self.draw_row(c, x, y, self.SALES_BOX_FOT_COLS, (_("* Sale was FOT originally"),))

        c.rect(x, top_y, self.SALES_BOX_WIDTH, y - top_y)

        y += self.PAGE_MARGIN

        totals = export_rows[-1]
        y += self.draw_row(c, x, y, self.SALES_BOX_TOTAL_COLS, 
                           (_("Total Sales"), totals.volume, totals.fot_price, totals.fob_price, totals.revenue))

        c.rect(x, top_y, self.SALES_BOX_WIDTH, y - top_y)

        return y - top_y

    def draw_local_sales_box(self, c, y):
        x = self.PAGE_MARGIN + self.PROD_BOX_WIDTH + self.SECTION_MARGIN
        top_y = y

        y += self.draw_box_header(c, x, y, _("Local Sales"),
                                  self.LOCAL_SALES_BOX_HEADER_COLS,
                                  (_("Buyer"), _("%s") % self.weight_abbreviation, _("%s/%s") % (self.curr_abbreviation, self.weight_abbreviation),
                                   _("%s/%s") % (self.curr_abbreviation, self.weight_abbreviation)))

        export_rows = self.sales.get_export_rows()
        local_rows = self.sales.get_local_rows()
        if len(local_rows) > 1:
            for (i, sale) in enumerate(local_rows[:-1]):
                if not self.show_buyers:
                    buyer = "Buyer %d" % (i+len(export_rows)+1)
                else:
                    buyer = None

                y += self.draw_row(c, x, y, self.LOCAL_SALES_BOX_COLS,
                                   (sale.get_buyer_display(buyer), sale.volume, sale.price, sale.revenue))
            
        c.rect(x, top_y, self.SALES_BOX_WIDTH, y - top_y)

        y += self.PAGE_MARGIN

        totals = local_rows[-1]
        y += self.draw_row(c, x, y, self.LOCAL_SALES_BOX_TOTAL_COLS, 
                           (_("Total Local Sales"), totals.volume, totals.price, totals.revenue))

        c.rect(x, top_y, self.SALES_BOX_WIDTH, y - top_y)

        return y - top_y

    def draw_working_capital(self, c, y):
        x = self.PAGE_MARGIN + self.PROD_BOX_WIDTH + self.SECTION_MARGIN
        top_y = y

        y += self.draw_box_header(c, x, y, _("Working Capital"), self.WORKING_CAPITAL_COLS, None)
        
        utilized = None
        expense_categories = self.expenses.get_categories()
        if expense_categories:
            utilized = expense_categories[0].value

        working_capital = CV(self.report.working_capital)
        working_capital_repaid = CV(self.report.working_capital_repaid)

        y += self.draw_row(c, x, y, self.WORKING_CAPITAL_COLS, (_("Working Capital Received"), working_capital))
        y += self.draw_row(c, x, y, self.WORKING_CAPITAL_COLS, (_("Working Capital Utilized"), utilized))
        y += self.draw_row(c, x, y, self.WORKING_CAPITAL_COLS, (_("Working Capital Repaid"), working_capital_repaid))
        if self.report_mode != 'CR':
            # We don't want to draw the Unused working capital for the credit report (According to the requirement)
            y += self.draw_row(c, x, y, self.WORKING_CAPITAL_COLS, (_("Unused Working Capital"), self.cash.unused_working_capital))

        c.rect(x, top_y, self.SALES_BOX_WIDTH, y - top_y)

        return y - top_y

    def draw_cash_box(self, c, y):
        # if there is no source of cash or use of cash, then just return
        if not self.cash.get_sources() and not self.cash.get_uses():
            return 0

        x = self.PAGE_MARGIN
        width = self.EXPENSE_BOX_WIDTH
        top_y = y

        y += self.PAGE_MARGIN

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER1_COLS,
                           ("", self.report.wetmill.name, _("Average Client"), _("Best Client")))

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER2_COLS,
                           ("", _("Total (%s)") % self.curr_abbreviation, _("%s/%s Cherry") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Cherry") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Cherry") % (self.curr_abbreviation, self.weight_abbreviation)))

        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN

        if self.cash.get_sources():
            y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS, (_("SOURCES OF CASH"),))
            for cashsource in self.cash.get_sources():
                y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.CASH_COLS,
                                   (cashsource.name, cashsource.total, cashsource.total, cashsource.slug(), cashsource.slug()))

        if self.cash.get_uses():
            y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS, (_("USE OF CASH"),))
            for use in self.cash.get_uses():
                y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.CASH_COLS,
                                   (use.name, use.total, use.total, use.slug(), use.slug()))

        c.rect(x, top_y, width, y - top_y)

        return y - top_y

    def draw_farmer_box(self, c, y):
        predicted_height = self.get_line_height() * (7 + (len(self.farmer.get_rows())))
        if y + predicted_height > self.PAGE_HEIGHT:
            c.showPage()
            y = self.PAGE_MARGIN

        x = self.PAGE_MARGIN
        width = self.EXPENSE_BOX_WIDTH
        top_y = y

        y += self.draw_box_header(c, x, y, _("Farmer Payment"), self.FARMER_COLS, None)

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER1_COLS,
                           ("", self.report.wetmill.name, _("Average Client"), _("Best Client")))

        exchange_legend = "%d %s = 1 %s" % (self.exchange, self.local_currency.abbreviation, self.usd.abbreviation)

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER2_COLS,
                           (exchange_legend, _("%s/%s Cherry") % (self.local_abbreviation, self.weight_abbreviation), _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation)))

        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN

        for row in self.farmer.get_rows():
            label = row.label
            if row.row_for == 'MEM':
                label = _("%s (Members)") % label
            elif row.row_for == 'NON':
                label = _("%s (Non-Members)") % label

            cols = self.FARMER_COLS
            if row.is_total:
                cols = self.FARMER_TOTAL_COLS

            y += self.draw_row(c, x, y, cols,
                               (label, row.value, row.value, row.slug(), row.slug()))

        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN

        if self.farmer.farmer_percentage:
            label = _("Proportion of Profit Paid to Farmers: %d%%") % self.farmer.farmer_percentage
            y += self.draw_row(c, x, y, self.FARMER_SUMMARY_COLS, (label,))

        if self.report.season.has_members:
            if self.farmer.member_price_share and self.farmer.non_member_price_share:
                label = _("Farmer Share of Average Sale Price %(member_share)d%% (Members), %(non_member_share)d%% (Non-Members)") % dict(member_share=self.farmer.member_price_share, non_member_share=self.farmer.non_member_price_share)
                y += self.draw_row(c, x, y, self.FARMER_SUMMARY_COLS, (label,))
        else:
            if self.farmer.price_share:
                label = _("Farmer Share of Average Sale Price %d%%") % self.farmer.price_share
                y += self.draw_row(c, x, y, self.FARMER_SUMMARY_COLS, (label,))

        c.rect(x, top_y, width, y - top_y)

        return y - top_y

    def draw_expenses(self, c, y):
        x = self.PAGE_MARGIN
        width = self.EXPENSE_BOX_WIDTH
        top_y = y

        y += self.draw_box_header(c, x, y, _("Profit and Loss"), self.EXPENSE_BOX_COLS, None)

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER1_COLS,
                           ("", self.report.wetmill.name, _("Average Client"), _("Best Client")))

        y += self.draw_row(c, x, y, self.EXPENSE_HEADER2_COLS,
                           ("", _("Total (%s)") % self.curr_abbreviation, _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation), _("%s/%s Green") % (self.curr_abbreviation, self.weight_abbreviation)))

        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN

        # the number of stars to use in our legend, increments on each calculated expense
        stars = 2

        # our list of the legend items we need to put at the end of our expense box
        legend = []

        if self.report.season.has_misc_revenue:
            y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.EXPENSE_CATEGORY_COLS,
                               (_("Total Coffee Revenue"), self.expenses.sales_revenue, self.expenses.sales_revenue,
                                "sales_revenue", "sales_revenue"))
            y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.EXPENSE_CATEGORY_COLS,
                               (_("Miscellaneous Revenue"), self.expenses.misc_revenue, self.expenses.misc_revenue,
                                "misc_revenue", "misc_revenue"))

        y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS,
                        (_("TOTAL REVENUE"), self.expenses.total_revenue, self.expenses.total_revenue, 'total_revenue', 'total_revenue'))

        for category in self.expenses.get_categories():
            # if this category is collapsed, don't show details
            if category.expense.collapse:
                y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.EXPENSE_CATEGORY_COLS,
                                   (category.name, category.value, category.value, category.slug(), category.slug()))

            # otherwise, draw all our children and totals
            else:
                y += self.draw_row(c, x+self.EXPENSE_CATEGORY_MARGIN, y, self.EXPENSE_CATEGORY_COLS,
                                   (category.name,))

                for child in category.children:
                    label = child.name
                    calculated_legend = child.get_calculated_legend()

                    if calculated_legend:
                        label += stars * "*"
                        legend.append(stars * "*" + " " + calculated_legend)
                        stars += 1

                    y += self.draw_row(c, x+self.EXPENSE_ROW_MARGIN, y, self.EXPENSE_ROW_COLS,
                                       (label, child.value, child.value, child.slug(), child.slug()))

                y += self.draw_row(c, x+self.EXPENSE_ROW_MARGIN, y, self.EXPENSE_CATEGORY_TOTAL_COLS,
                                   (_("Total %s") % category.name, category.value, category.value, category.slug(), category.slug()))

                # there is some advance data to show
                if category.non_advance_value().as_local(self.exchange) != category.value.as_local(self.exchange):
                    advance_slug = "%s__non_advance" % category.slug()

                    y += self.draw_row(c, x+self.EXPENSE_ROW_MARGIN, y, self.EXPENSE_CATEGORY_TOTAL_COLS,
                                       (_("Total Non-Advance Expenses"),
                                        category.non_advance_value(), category.non_advance_value(),
                                        advance_slug, advance_slug))

            y += self.PAGE_MARGIN

        y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS,
                                 (_("TOTAL EXPENSES"), self.expenses.total, self.expenses.total, 'total_expenses', 'total_expenses'))

        y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS,
                                 (_("FOREIGN EXCHANGE LOSS (GAIN)"), self.expenses.total_forex_loss,
                                  self.expenses.total_forex_loss, 'total_forex_loss', 'total_forex_loss'))

        y += self.draw_row(c, x, y, self.EXPENSE_TOTAL_COLS,
                                 (_("TOTAL PROFIT (LOSS)"), self.expenses.total_profit, self.expenses.total_profit, 
                                  'total_profit', 'total_profit'))

        if legend:
            y += self.PAGE_MARGIN
            for label in legend:
                y += self.draw_row(c, x, y, self.EXPENSE_FOT_COLS, (label,))

        c.rect(x, top_y, width, y - top_y)

        return y - top_y

    def draw_historical_performance(self, c, y):
        self.report.working_capital_two_seasons_ago = self.report.working_capital_one_season_ago = '-'
        self.report.total_profitability_two_seasons_ago = self.report.total_profitability_one_season_ago = '-'
        self.report.total_sale_two_seasons_ago = self.report.total_sale_one_season_ago = '-'
        self.report.working_capital_repaid_pct_two_seasons_ago = self.report.working_capital_repaid_pct_one_season_ago = '-'

        x = self.PAGE_MARGIN
        width = self.EXPENSE_BOX_WIDTH
        top_y = y

        y += self.draw_box_header(c, x, y, _("Historical Performance"), self.EXPENSE_BOX_COLS, None)

        last_two_seasons = self.report.season.get_previous_two_seasons()
        one_season_ago = last_two_seasons[0] if last_two_seasons and last_two_seasons[0] else None
        two_seasons_ago = last_two_seasons[1] if last_two_seasons and last_two_seasons[1] else None

        one_season_ago_name = None
        two_seasons_ago_name = None

        one_season_ago_exchange = two_seasons_ago_exchange = None

        if one_season_ago:
            one_season_ago_name = one_season_ago.name + ' Season'
            one_season_ago_report = Report.load_for_wetmill_season(wetmill=self.report.wetmill, season=one_season_ago)
            if one_season_ago_report:
                one_season_ago_exchange = one_season_ago_report.season.exchange_rate
                self.report.working_capital_one_season_ago = CV(one_season_ago_report.working_capital)
                self.report.working_capital_repaid_pct_one_season_ago = self.decimal_to_string(one_season_ago_report.working_capital_repaid/one_season_ago_report.working_capital*100, True) + '%'

                one_season_ago_production = ProductionBox(one_season_ago_report)
                one_season_ago_sales = SalesBox(one_season_ago_report, self.report_currency)
                one_season_ago_expenses = ExpenseBox(one_season_ago_report, one_season_ago_production, one_season_ago_sales, self.report_currency)
                
                one_season_ago_local_rows = one_season_ago_sales.get_local_rows()
                one_season_ago_export_rows = one_season_ago_sales.get_export_rows()
                
                one_season_ago_local_totals = one_season_ago_local_rows[-1]
                one_season_ago_export_totals = one_season_ago_export_rows[-1]

                self.report.total_sale_one_season_ago = CV(one_season_ago_local_totals.revenue + one_season_ago_export_totals.revenue)
                self.report.total_profitability_one_season_ago = CV(one_season_ago_expenses.total_profit)

        if two_seasons_ago:
            two_seasons_ago_name = two_seasons_ago.name + ' Season'
            two_seasons_ago_report = Report.load_for_wetmill_season(wetmill=self.report.wetmill, season=two_seasons_ago)
            if two_seasons_ago_report:
                two_seasons_ago_exchange = two_seasons_ago_report.season.exchange_rate
                self.report.working_capital_two_seasons_ago = CV(two_seasons_ago_report.working_capital)
                self.report.working_capital_repaid_pct_two_seasons_ago = self.decimal_to_string(two_seasons_ago_report.working_capital_repaid/two_seasons_ago_report.working_capital*100, True) + '%'

                two_seasons_ago_production = ProductionBox(two_seasons_ago_report)
                two_seasons_ago_sales = SalesBox(two_seasons_ago_report, self.report_currency)
                two_seasons_ago_expenses = ExpenseBox(two_seasons_ago_report, two_seasons_ago_production, two_seasons_ago_sales, self.report_currency)

                two_seasons_ago_local_rows = two_seasons_ago_sales.get_local_rows()
                two_seasons_ago_export_rows = two_seasons_ago_sales.get_export_rows()

                two_seasons_ago_local_totals = two_seasons_ago_local_rows[-1]
                two_seasons_ago_export_totals = two_seasons_ago_export_rows[-1]

                self.report.total_sale_two_seasons_ago = CV(two_seasons_ago_local_totals.revenue + two_seasons_ago_export_totals.revenue)
                self.report.total_profitability_two_seasons_ago = CV(two_seasons_ago_expenses.total_profit)

        local_rows = self.sales.get_local_rows()
        export_rows = self.sales.get_export_rows()

        local_totals = local_rows[-1]
        export_totals = export_rows[-1]

        current_season_name = self.report.season.name + ' Season'
        current_season_working_capital = '-'
        if self.report.working_capital:
            current_season_working_capital = CV(self.report.working_capital)
        current_season_repaid_pct = '-'
        if self.report.working_capital_repaid and self.report.working_capital:
            current_season_repaid_pct = "%s" % self.decimal_to_string(self.report.working_capital_repaid/self.report.working_capital*100, True) + "%"
        current_season_total_profit = CV(self.expenses.total_profit)
        current_season_total_sales = CV(local_totals.revenue + export_totals.revenue)

        y += self.draw_row(c, x, y, self.HISTORICAL_SECTION_BOX_COLS_HDR, (None, two_seasons_ago_name, one_season_ago_name, current_season_name))
        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN

        y += self.draw_row_historical(c, x, y, self.HISTORICAL_SECTION_BOX_COLS_CUR, (_("Working Capital Received"), self.report.working_capital_two_seasons_ago, self.report.working_capital_one_season_ago, current_season_working_capital), one_season_ago_exchange, two_seasons_ago_exchange)
        y += self.draw_row_historical(c, x, y, self.HISTORICAL_SECTION_BOX_COLS, (_("Working Capital Repayment %"), self.report.working_capital_repaid_pct_two_seasons_ago, self.report.working_capital_repaid_pct_one_season_ago, current_season_repaid_pct), one_season_ago_exchange, two_seasons_ago_exchange)
        y += self.draw_row_historical(c, x, y, self.HISTORICAL_SECTION_BOX_COLS_CUR, (_("Total Sales (%s)") % self.curr_abbreviation, self.report.total_sale_two_seasons_ago, self.report.total_sale_one_season_ago, current_season_total_sales), one_season_ago_exchange, two_seasons_ago_exchange)
        y += self.draw_row_historical(c, x, y, self.HISTORICAL_SECTION_BOX_COLS_CUR, (_("Total Profit"), self.report.total_profitability_two_seasons_ago, self.report.total_profitability_one_season_ago, current_season_total_profit), one_season_ago_exchange, two_seasons_ago_exchange)
        c.rect(x, top_y, width, y - top_y)

        return y - top_y


    def gauge_rotation(self, minimum, maximum, current):
        reverse = False

        # are we drawing with the minimum value to the left?
        if minimum > maximum:
            reverse = True;
            (minimum, maximum) = (maximum, minimum)

        # recalibrate if our value is out of range
        if current < minimum:
            minimum = current

        if current > maximum:
            maximum = current

        # calculate the rotation point depending on min, max and current
        try:
            if reverse:
                degree = Decimal(260) - (((current-minimum) / (maximum - minimum)) * Decimal(160))
            else:
                degree = ((Decimal(current-minimum) / (maximum - minimum)) * Decimal(160)) + Decimal(100)
        except:
            degree = 0

        # make sure that the dial doesn't leach the unvaluable space
        # in the other words rotates just 90 degrees to left and right
        if degree > 90 and degree <= 270:
            degree -= 180

        if reverse:
            return (degree, maximum, minimum)
        else:
            return (degree, minimum, maximum)

    def round_value(self, value):
        if not value is None and hasattr(value, 'quantize'):
            return str(value.quantize(Decimal(".01", ROUND_HALF_UP)))
        else:
            return str(value)

    def draw_gauge(self,c, x, y, width, minimum, maximum, value, subtitle, primary_font_size, 
                   secondary_font_size, gauge_type='ratio', value_unit='', force_weight_ratio=False):
        """
        Draw the gauge
        """
        top_y = y

        # gauge images width and height as they will never change
        # these values are part of the pdf images if any image changed this also should
        BG_WIDTH = 400
        BG_HEIGHT = 200
        DIAL_WIDTH = 16
        DIAL_HEIGHT = 160
        DIAL_CAP_WIDTH = 58
        DIAL_CAP_HEIGHT = 52

        # useful midpoints
        bg_mid_width = BG_WIDTH/2
        dial_mid_width = DIAL_WIDTH/2
        dial_cap_mid_width = DIAL_CAP_WIDTH/2
        dial_cap_mid_height = DIAL_CAP_HEIGHT/2

        # this is the restore point before rotation
        c.saveState()

        # translate to the start of our world
        c.translate(x, y)

        scale = width / float(BG_WIDTH)
        c.scale(scale, scale)

        # draw the gauge background image according to the canvas size
        c.saveState()
        c.scale(1.0,-1.0)
        c.drawImage(self.GAUGE_BG, 0, -BG_HEIGHT, mask='auto')
        c.restoreState()

        # anything drawn below will be postioned at the bottom center
        c.translate(bg_mid_width, BG_HEIGHT)

        # if any of these values are null display nothing
        if minimum is None or maximum is None or value is None:
            minimum = maximum = value = None
        else:
            # calculate the rotation point
            if force_weight_ratio:
                # consider the weight ratio
                degree, minimum, maximum = self.gauge_rotation(minimum * self.weight_ratio, maximum * self.weight_ratio, value * self.weight_ratio)
            else:
                degree, minimum, maximum = self.gauge_rotation(minimum, maximum, value)

            # draw the needle
            c.rotate(float(degree))
            c.saveState()
            c.scale(1.0,-1.0)
            c.drawImage(self.GAUGE_DIAL, -dial_mid_width,0, mask='auto')
            c.restoreState()

            c.saveState()
            c.scale(1.0,-1.0)
            c.drawImage(self.GAUGE_DIAL_CAP, -dial_cap_mid_width,-dial_cap_mid_height, mask='auto')
            c.restoreState()
    
        # restore the current positioning
        c.restoreState()

        min_max_offset = width/10

        gauge_height = scale*BG_HEIGHT - 2 * getDescent(self.BOX_FONT_BOLD, primary_font_size)
        self.set_font(c, self.BOX_FONT_BOLD, primary_font_size)

        # handle different behavior of the gauge values
        currency = self.report_currency

        if minimum is None or maximum is None or value is None:
            minimum = maximum = value = ''
        else:
            if force_weight_ratio:
                value = value * self.weight_ratio

            if gauge_type == "percentage":
                minimum = "%s%%" % minimum
                maximum = "%s%%" % maximum
                value = "%s%%" % value
            elif gauge_type == "currency":
                minimum = self.format_value(CV(minimum), self.CURR)
                maximum = self.format_value(CV(maximum), self.CURR)
                value = self.format_value(CV(value), self.CURR)
            else:
                minimum = self.round_value(minimum)
                maximum = self.round_value(maximum)
                value = self.round_value(value)
            
        label_y = y + gauge_height + getAscent(self.BOX_FONT_BOLD, primary_font_size)

        c.drawCentredString(x+min_max_offset, label_y, minimum)
        c.drawCentredString(x+width-min_max_offset, label_y, maximum)

        label_y = y + gauge_height + scale*dial_cap_mid_height - getDescent(self.BOX_FONT_BOLD, secondary_font_size) + getAscent(self.BOX_FONT_BOLD, secondary_font_size)

        line_height = getAscent(self.BOX_FONT_BOLD, secondary_font_size) - 2 * getDescent(self.BOX_FONT_BOLD, secondary_font_size)
        
        self.set_font(c, self.BOX_FONT_BOLD, secondary_font_size)        
        c.drawCentredString(x+width/2, label_y, subtitle)
        label_y += line_height
        c.drawCentredString(x+width/2, label_y, "%s %s" % (value, value_unit))
        label_y += line_height

        return label_y - top_y

    def lat_to_x(self, country, latitude):
        if country.name == 'Ethiopia':
            offset = 256 << 6-1
            return offset - offset/math.pi * math.log((1 + math.sin(latitude * math.pi/180)) / (1 - math.sin(latitude * math.pi /180))) / 2
        elif country.name == 'Kenya':
            offset = 256 << 6-1
            return offset - offset/math.pi * math.log((1 + math.sin(latitude * math.pi/180)) / (1 - math.sin(latitude * math.pi /180))) / 2
        elif country.name == 'Rwanda':
            offset = 256 << 9-1
            return offset - offset/math.pi * math.log((1 + math.sin(latitude * math.pi/180)) / (1 - math.sin(latitude * math.pi /180))) / 2
        else:
            offset = 256 << 6-1
            return offset - offset/math.pi * math.log((1 + math.sin(latitude * math.pi/180)) / (1 - math.sin(latitude * math.pi /180))) / 2

    def lng_to_y(self, country, longitude):
        if country.name == 'Ethiopia':
            offset = 256 << 6-1
            return offset + (offset * longitude / 180)
        elif country.name == 'Kenya':
            offset = 256 << 6-1
            return offset + (offset * longitude / 180)
        elif country.name == 'Rwanda':
            offset = 256 << 9-1
            return offset + (offset * longitude / 180)
        else:
            offset = 256 << 6-1
            return offset + (offset * longitude / 180)

    def draw_country_map(self, c, x, y, width, country, lat, lng):
        top_y = y
        
        # assign the map constant to its country depending based on the country name
        country_map = eval("self." + country.name.upper() + "_MAP")
        BG_HEIGHT = 235

        c.saveState()
        # this is the starting cordinate of our min world
        c.translate(x, y)

        # draw the country map
        c.saveState()
        c.scale(1.0,-1.0)
        country_coordinates = c.drawImage(country_map, 0, -BG_HEIGHT, mask='auto')
        c.restoreState()

        country_width = country_coordinates[0]
        country_height = country_coordinates[1]

        # decide north east coordinate and ratio by country
        if country.name.lower() == 'rwanda':
            ne_coordinates = (-0.95851234611764, 28.824255738281252)
            ratio = country_width/float(771)
        elif country.name.lower() == 'kenya':
            ne_coordinates = (-0.95851234611764, 28.824255738281252)
            ratio = country_width/float(771)
        elif country.name.lower() == 'ethiopia':
            ne_coordinates = (-0.95851234611764, 28.824255738281252)
            ratio = country_width/float(771)
        else:
            ne_coordinates = (-0.95851234611764, 28.824255738281252)
            ratio = country_width/float(771)

        if lat and lng:
            top = self.lat_to_x(country, ne_coordinates[0]) 
            left = self.lng_to_y(country, ne_coordinates[1])

            lat = self.lat_to_x(country, float(lat)) - top
            lng = self.lng_to_y(country, float(lng)) - left

            # show where exactly the location on the map
            c.setFillColorRGB(0,0,0)
            c.circle(lng*ratio, lat*ratio, 4, fill=1)

        c.restoreState()
        
        return BG_HEIGHT

    def draw_farmer_payment_gauge(self, c, x, y):
        width = self.FARMER_PAYMENT_BOX_WIDTH
        top_y = y

        y += self.draw_box_header(c, x, y, _("Total Farmer Payment"), self.FARMER_PAYMENT_BOX_HEADER_COLS , None)

        left_value = self.report.season.farmer_payment_left * self.weight_ratio
        right_value = self.report.season.farmer_payment_right * self.weight_ratio
        value = self.per_weight_unit_cherry(self.farmer.total_paid.as_local(self.exchange))

        gauge_width = width - self.GAUGE_MARGIN*2
        gauge_subtitle = "Total farmer Payment"
        y += self.draw_gauge(c, x+self.GAUGE_MARGIN, y+self.GAUGE_MARGIN, gauge_width, 
                             left_value, right_value, value, gauge_subtitle, 
                             10, 10, "currency", "/ %s Cherry" % self.weight_abbreviation)

        y += self.PAGE_MARGIN
        
        return y - top_y
    
    def draw_wetmill_location(self, c, x, y):

        wetmill = self.report.wetmill
        country = wetmill.country
        lat = wetmill.latitude
        lng = wetmill.longitude

        if country.name.lower() == 'rwanda':
            width = 263
        elif country.name.lower() == 'kenya':
            width = 206
        elif country.name.lower() == 'ethiopia':
            width = 298
        else:
            width = 248

        top_y = y

        # providing enough space between text and the map
        MAP_PADDING = 75
        TINY_PADDING = 2
        # draw the header with title of the box
        y += self.draw_box_header(c, x, y, _("Location"), self.FARMER_PAYMENT_BOX_HEADER_COLS , None)

        # set the title of the text section of the location box
        self.set_font(c, self.BOX_FONT_BOLD, 9)
        y += self.get_ascent() + self.PAGE_MARGIN
        c.drawString(x+self.PAGE_MARGIN*2,y,"%s Wet Mill" % wetmill.name.capitalize())

        # the y position of the map exactly under the title of the text section
        map_y = y + self.PAGE_MARGIN

        # all info related to this wetmill 
        self.set_font(c, self.BOX_FONT_BOLD, 7)

        if self.report.farmers is not None:
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            y += self.get_ascent() + self.PAGE_MARGIN + TINY_PADDING
            c.drawString(x+self.PAGE_MARGIN*2,y,"Farmers")
            self.set_font(c, self.BOX_FONT, 7)
            y += self.get_ascent() + self.PAGE_MARGIN
            c.drawString(x+self.PAGE_MARGIN*2, y, str(self.report.farmers))

        if wetmill.province is not None:
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            y += self.get_ascent() + self.PAGE_MARGIN + TINY_PADDING
            c.drawString(x+self.PAGE_MARGIN*2,y,"Province")
            self.set_font(c, self.BOX_FONT, 7)
            y += self.get_ascent() + self.PAGE_MARGIN
            c.drawString(x+self.PAGE_MARGIN*2,y,str(wetmill.province))
            y += self.get_ascent() + self.PAGE_MARGIN

        if wetmill.altitude is not None:
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            y += self.get_ascent() + self.PAGE_MARGIN + TINY_PADDING
            c.drawString(x+self.PAGE_MARGIN*2,y,"Altitude")
            self.set_font(c, self.BOX_FONT, 7)
            y += self.get_ascent() + self.PAGE_MARGIN
            c.drawString(x+self.PAGE_MARGIN*2,y,str(wetmill.altitude))

        if wetmill.latitude is not None or wetmill.longitude is not None:
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            y += self.get_ascent() + self.PAGE_MARGIN + TINY_PADDING
            c.drawString(x+self.PAGE_MARGIN*2,y,"Latitude")
            self.set_font(c, self.BOX_FONT, 7)
            y += self.get_ascent() + self.PAGE_MARGIN
            c.drawString(x+self.PAGE_MARGIN*2,y, str(wetmill.latitude.quantize(Decimal(".0001"))))
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            y += self.get_ascent() + self.PAGE_MARGIN + TINY_PADDING
            c.drawString(x+self.PAGE_MARGIN*2,y,"Longitude")
            self.set_font(c, self.BOX_FONT, 7)
            y += self.get_ascent() + self.PAGE_MARGIN
            c.drawString(x+self.PAGE_MARGIN*2,y,str(wetmill.longitude.quantize(Decimal(".0001"))))

        # reduce the size of the map 25% for it to fit in the box
        # side by side with wetmill description text
        SCALE = 0.75
        c.saveState()
        c.scale(SCALE, SCALE)
        height = self.draw_country_map(c, x/SCALE+self.PAGE_MARGIN*2 + MAP_PADDING, map_y/SCALE, width, country, lat, lng)
        c.restoreState()

        return SCALE * (height + map_y) + self.PAGE_MARGIN*2

    def draw_performance_dashboard(self, c, x, y):
        width = self.PERFORMANCE_BOX_HEADER_WIDTH
        top_x = x
        top_y = y

        y += self.draw_box_header(c, x, y, _("Performance Dashboard"), self.PERFORMANCE_BOX_HEADER_COLS , None)

        gauge_width = (width - self.EXPENSE_CATEGORY_MARGIN*10)/4

        gauge_subtitle = _("Wetmill Utilization")
        x += self.EXPENSE_CATEGORY_MARGIN*2
        self.draw_gauge(c, x, y+self.GAUGE_MARGIN, gauge_width, 
                        0, 100, 
                        self.production.utilization, 
                        gauge_subtitle, 7, 7, "percentage")

        if self.production.has_top_grade:
            gauge_subtitle = _("Cherry to Top Grade Ratio")
        else:
            gauge_subtitle = _("Cherry to Green Ratio")
        x += gauge_width + self.EXPENSE_CATEGORY_MARGIN*2
        self.draw_gauge(c, x, y+self.GAUGE_MARGIN, gauge_width, 
                        self.season.cherry_ratio_left, self.season.cherry_ratio_right, 
                        self.production.cherry_to_top_grade_ratio, 
                        gauge_subtitle, 7, 7)

        gauge_subtitle = _("Total Costs")
        x += gauge_width + self.EXPENSE_CATEGORY_MARGIN*2
        self.draw_gauge(c, x, y+self.GAUGE_MARGIN, gauge_width, 
                        self.season.total_costs_left, self.season.total_costs_right, 
                        self.expenses.production_cost.as_local(self.exchange),
                        gauge_subtitle, 7, 7, "currency", _("/ %s Green") % self.weight_abbreviation, True)

        gauge_subtitle = _("Sale Price")
        x += gauge_width + self.EXPENSE_CATEGORY_MARGIN*2
        y += self.draw_gauge(c, x, y+self.GAUGE_MARGIN, gauge_width, 
                             self.season.sale_price_left, self.season.sale_price_right, 
                             self.sales.fot_price.as_local(self.exchange), 
                             gauge_subtitle, 7, 7, "currency", _("/ %s Green(FOT)") % self.weight_abbreviation, True)

        y += self.PAGE_MARGIN

        c.rect(top_x, top_y, width, y - top_y)

        return y - top_y

    def nice_number(self, value, adjust):
        """
        Returns the value adjusted according to value of adjust variable
        """
        if value <= 0:
            return 0

        # exponent of value
        exp = math.floor(math.log10(value))

        # fractional part of value
        f = float(value) / math.pow(10, exp)

        if adjust:
            if f < 1.5:
                nf = 1
            elif f < 3:
                nf = 2
            elif f < 7:
                nf = 5
            else:
                nf = 10
        else:
            if f <= 1:
                nf = 1
            elif f <= 2:
                nf = 2
            elif f <= 5:
                nf = 5
            else:
                nf = 10

        return nf * math.pow(10, exp)

    def draw_yaxis(self, c, x, y, width, height, minimum, maximum, ticks, percentage, currency):
        """
        Draw the y axis
        """
        top_y = y

        minimum = float(str(minimum))
        maximum = float(str(maximum))

        SHORT_DISTANCE = 8
        DISTANCE = 10

        # get range on numbers between min and max
        value_range = self.nice_number(maximum-minimum, False)

        # tick mark spacing
        d = self.nice_number(value_range/(ticks-1),True)

        # graph range min and max
        if d > 0:
            gmin = math.floor(minimum/d)*d
            gmax = math.ceil(maximum/d)*d

            # change the value range to exact to one unit and the value them in percentages
            if percentage:
                gmax = 1

        else:
            gmin = 0
            gmax = 0

        curr = float(gmax)

        # draw actual axis one tick at a time
        c.line(x+DISTANCE, y, x+DISTANCE, y+height)

        while curr > (gmin + .5 * d):
            if percentage:
                c.drawCentredString(x,y, str(int(curr*100)))
            else:
                c.drawCentredString(x,y, str(curr))

            curr -= d
            c.line(x+DISTANCE,y,x+SHORT_DISTANCE,y)
            y += height/(gmax/d)

        c.drawCentredString(x,y, "0")
        c.line(x+DISTANCE,y,x+SHORT_DISTANCE,y)

        return height

    def draw_bar_value(self, c, bar_top, bar_base, value_pos_x, value, percentage=False):
        if not percentage and value:
            value = value.quantize(Decimal(".01"), ROUND_HALF_UP)

        if bar_top >= bar_base + self.PAGE_MARGIN*2:
            self.set_black(c)
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            value = str(int(value*100)) + "%" if percentage else str(value)
            c.drawCentredString(value_pos_x, bar_top-self.PAGE_MARGIN, value)
        else:
            self.set_white(c)
            self.set_font(c, self.BOX_FONT_BOLD, 7)
            value = str(int(value*100)) + "%" if percentage else str(value)
            c.drawCentredString(value_pos_x, bar_top+self.PAGE_MARGIN*2, value)
            self.set_black(c)

    def draw_bar_graph(self, c, x, y, minimum, wetmill_value, tns_value, title, ticks=10, percentage=False):
        if minimum is None:
            minimum = 0
            
        if wetmill_value is None:
            wetmill_value = 0

        if tns_value is None:
            tns_value = 0

        if percentage:
            wetmill_value = wetmill_value / Decimal(100)
            tns_value = tns_value / Decimal(100)
            
        top_x = x
        top_y = y
        BAR_HEIGHT = 160
        width = self.BARGRAPH_BOX_HEADER_WIDTH
        maximum = max(wetmill_value, tns_value)

        # get range on numbers between min and max
        value_range = self.nice_number(maximum, False)

        # tick mark spacing
        d = self.nice_number(value_range/(ticks-1),True)

        # graph range min and max
        if d > 0:
            gmax = math.ceil(float(maximum)/d)*d

            # change the value range to be exact to one unit and then value them in percentages
            if percentage:
                gmax = 1
        else:
            gmax = 0

        if gmax > 0:
            wetmill_height = float(wetmill_value) * BAR_HEIGHT / gmax
            tns_height = float(tns_value) * BAR_HEIGHT / gmax
        else:
            wetmill_height = 0
            tns_height = 0

        # draw the box header
        y += self.draw_box_header(c, x, y, title, self.BARGRAPH_BOX_HEADER_COLS , None) + self.PAGE_MARGIN

        BAR_WIDTH = 50
        BAR_MARGIN = 30
        bar_text_width = BAR_WIDTH + self.PAGE_MARGIN*2
        bar_x = x + BAR_MARGIN
        bar_y = y
        
        # draw y axis
        y += self.draw_yaxis(c, x+self.PAGE_MARGIN*2, y, width-self.PAGE_MARGIN*2, BAR_HEIGHT, str(minimum), str(maximum), ticks, percentage, None)
        # draw x axis
        c.line(x+self.PAGE_MARGIN*4,y,x+width-self.PAGE_MARGIN*4,y)

        c.setFillColorRGB(0,0,0)

        bar_height_diff = y-bar_y - wetmill_height
        bar_base = y-bar_y - bar_height_diff
        wetmill_text_x = bar_x - self.PAGE_MARGIN
        
        # draw the first bar for this wetmill
        c.rect(bar_x, bar_y+bar_height_diff, BAR_WIDTH, bar_base, fill=True)
        self.draw_bar_value(c, bar_y+bar_height_diff, bar_y+bar_base, bar_x+BAR_WIDTH/2, wetmill_value, percentage)

        bar_x += BAR_MARGIN + BAR_WIDTH
        bar_height_diff = y-bar_y-tns_height
        bar_base = y-bar_y-bar_height_diff
        tns_text_x = bar_x - self.PAGE_MARGIN

        # draw the second bar for technoserve average
        c.rect(bar_x, bar_y+bar_height_diff, BAR_WIDTH, bar_base, fill=True)
        self.draw_bar_value(c, bar_y+bar_height_diff, bar_y+bar_base, bar_x+BAR_WIDTH/2, tns_value, percentage)

        y += self.PAGE_MARGIN
        wetmill_season_name = "%s (%s)" % (self.report.wetmill.name, self.report.season.name) 

        # draw the bar subtitle under the x axis 
        left = self.wrap_word(c, wetmill_text_x, y, bar_text_width, 'center', wetmill_season_name)
        right = self.wrap_word(c, tns_text_x, y, bar_text_width, 'center', _("Average TechnoServe"))

        # decide on which one is strong for the container rectangle
        y += max(left, right)

        # draw the container rectangle
        c.rect(top_x, top_y, width, y - top_y)

        return y-top_y

    def draw_legend_element(self, c, x, y, color_value, title):
        c.setFillColorRGB(color_value, color_value,color_value)
        length = 5
        limit = 150
        y += self.get_ascent() - getDescent(self.BOX_FONT_BOLD, self.BOX_SIZE)
        c.rect(x, y, length, length, fill=True, stroke=False)
        c.setFillColorRGB(0,0,0)
        y += self.wrap_word(c, x+length+self.PAGE_MARGIN, y, limit, "left", title)

        return y

    def draw_stacked_bar_values(self, c, x, bar_center, y, heights, values, colors):
        TINY_PADDING = 2
        NORMAL_PADDING = 10
        RECT_WIDTH = 30
        
        text_height = self.get_ascent() - getDescent(self.BOX_FONT_BOLD, 6)
        minimum_y = y

        # print value are adjusted when the value string doesn't fit in the stack
        adjusted = False

        for count, height in enumerate(heights):
            if height <= text_height + NORMAL_PADDING:
                c.setFillColorRGB(colors[count][0], colors[count][1], colors[count][2])
                c.rect(x+bar_center-RECT_WIDTH/2, minimum_y-TINY_PADDING, RECT_WIDTH, -text_height-TINY_PADDING*2, fill=True, stroke=False)
                c.setFillColorRGB(1,1,1)

                label = self.report_currency.format(values[count])

                c.drawCentredString(x+bar_center, minimum_y-TINY_PADDING*2, label)
                adjusted = True
                minimum_y -= text_height + TINY_PADDING*2
            else:
                # as the last value was adjusted
                if adjusted: # pragma: no cover
                    # then remove the adjusted height 
                    minimum_y += text_height + TINY_PADDING

                label = self.report_currency.format(values[count])

                # draw the value with normal padding 'cause the text can fit in the stack
                c.drawCentredString(x+bar_center, minimum_y-height+NORMAL_PADDING, label)
                minimum_y -= height
        
    def draw_stacked_bar_graph(self, c, x, y, minimum, wetmill_values, tns_values, title, legend_titles, 
                               ticks=10, percentage=False):

        # in order to draw top to bottom in the same order as the order passed in we first
        # need to reverse our incoming arrays
        wetmill_values.reverse()
        tns_values.reverse()
        legend_titles.reverse()

        if minimum is None:
            minimum = 0
            
        # convert nones to zeros
        new_wetmill_values = []
        for value in wetmill_values:
            if value is None:
                value = 0

            if self.report_currency.currency_code == 'USD':
                new_wetmill_values.append(value / self.exchange)
            else:
                new_wetmill_values.append(value)

        # convert nones to zeros
        new_tns_values = []
        for value in tns_values:
            if value is None:
                value = 0

            value = value * self.weight_ratio

            if self.report_currency.currency_code == 'USD':
                new_tns_values.append(value / self.exchange)
            else:
                new_tns_values.append(value)

        top_x = x
        top_y = y
        BAR_HEIGHT = 180
        width = self.PERFORMANCE_BOX_HEADER_WIDTH
        maximum = max(sum(new_wetmill_values), sum(new_tns_values))

        # get range on numbers between min and max
        value_range = self.nice_number(maximum, False)

        # tick mark spacing
        d = self.nice_number(value_range/(ticks-1),True)

        # graph range min and max
        if d > 0:
            gmax = math.ceil(float(maximum)/d)*d

            # change the value range to be exact to one unit and then value them in percentages
            if percentage:
                gmax = 1
        else:
            gmax = 0

        if gmax > 0:
            wetmill_heights = []
            for value in new_wetmill_values:
                wetmill_heights.append(float(value*BAR_HEIGHT)/gmax)
            full_wetmill_height = sum(wetmill_heights)

            tns_heights = []
            for value in new_tns_values:
                tns_heights.append(float(value*BAR_HEIGHT)/gmax)
            full_tns_height = sum(tns_heights)
        else:
            wetmill_heights = []
            for value in new_wetmill_values:
                wetmill_heights.append(0)
            full_wetmill_height = sum(wetmill_heights)

            tns_heights = []
            for value in new_tns_values:
                tns_heights.append(0)
            full_tns_height = sum(tns_heights)

        # draw the box header
        y += self.draw_box_header(c, x, y, title, self.PERFORMANCE_BOX_HEADER_COLS , None) + self.PAGE_MARGIN

        BAR_WIDTH = 160
        BAR_MARGIN = 30

        bar_text_width = BAR_WIDTH + self.PAGE_MARGIN*2
        bar_x = x + BAR_MARGIN
        legend_x = x + 420
        legend_y = y + 60
        
        # draw y axis
        y += self.draw_yaxis(c, x+self.PAGE_MARGIN*2, y, width-self.PAGE_MARGIN*2, BAR_HEIGHT, 
                             str(minimum), str(maximum), ticks, percentage, None)

        # draw x axis
        c.line(x+self.PAGE_MARGIN*4,y,x+self.PAGE_MARGIN*4+bar_text_width*2+BAR_MARGIN,y)

        bottom_graph_y = y
        colors = [(0,0,0),(.2,.2,.2),(.4,.4,.4),(.6,.6,.6),(.1,.1,.1),(.3,.3,.3),(.5,.5,.5),(.7,.7,.7)]

        # draw the wetmill bars
        bar_y = bottom_graph_y
        for count,height in enumerate(wetmill_heights):
            wetmill_text_x = bar_x - self.PAGE_MARGIN
            # draw the first bar for this wetmill
            c.setFillColorRGB(colors[count][0], colors[count][1], colors[count][2])
            c.rect(bar_x, bar_y,BAR_WIDTH,-height, fill=True, stroke=False)
            c.setFillColorRGB(1,1,1)
            bar_y -= height

        # reset the bar y postion and draw the values on top of the bars
        bar_y = bottom_graph_y
        self.draw_stacked_bar_values(c, bar_x, BAR_WIDTH/2, bar_y,wetmill_heights,new_wetmill_values, colors)

        # draw the technoserve bars
        bar_x += BAR_MARGIN + BAR_WIDTH
        bar_y = bottom_graph_y
        for count, height in enumerate(tns_heights):
            tns_text_x = bar_x - self.PAGE_MARGIN
            c.setFillColorRGB(colors[count][0], colors[count][1], colors[count][2])
            c.rect(bar_x, bar_y,BAR_WIDTH,-height, fill=True, stroke=False)
            c.setFillColorRGB(1,1,1)
            bar_y -= height

        # reset the bottom position and draw the values on top of the bars
        bar_y = bottom_graph_y
        self.draw_stacked_bar_values(c, bar_x, BAR_WIDTH/2, bar_y,
                                     tns_heights, new_tns_values, colors)

        y += self.PAGE_MARGIN
        wetmill_season_name = "%s (%s)" % (self.report.wetmill.name, self.report.season.name) 

        # draw the bar subtitle under the x axis 
        self.set_font(c, self.BOX_FONT_BOLD, 7)
        c.setFillColorRGB(0,0,0)
        left = self.wrap_word(c, wetmill_text_x, y, bar_text_width, 'center', wetmill_season_name)
        right = self.wrap_word(c, tns_text_x, y, bar_text_width, 'center', _("Average TechnoServe"))

        # decide on which one is strong for the container rectangle
        y += max(left, right)

        # draw the legend with different shade of colors from light gray (.6) to full black (0)
        legend_titles.reverse()
        for count, legend in enumerate(legend_titles):
            legend_y = self.draw_legend_element(c, legend_x, legend_y, colors[len(legend_titles)-count-1][0], legend)

        # draw the container rectangle
        c.rect(top_x, top_y, width, y - top_y)

        return y - top_y
    
    def draw_wetmill_attributes(self, c, y):
        top_y = y

        self.set_black(c)
        self.set_font(c, self.BOX_FONT_BOLD, self.BOX_SIZE)
        
        # draw our province name if we have one
        if self.report.wetmill.province and self.report.wetmill.province.name:
            c.drawString(self.PAGE_MARGIN, y+self.get_ascent(), _("Province: ") + self.report.wetmill.province.name)
            y += self.get_line_height()

        # draw our csp name if we have one
        csp = self.report.wetmill.get_csp_for_season(self.report.season)
        if csp:
            c.drawString(self.PAGE_MARGIN, y+self.get_ascent(), _("Coffee Service Provider: ") + csp.name)
            y += self.get_line_height()

        return y - top_y

    def draw_page_one(self, c):
        # start the page
        current_x = self.PAGE_MARGIN 
        current_y = self.PAGE_MARGIN

        # our main header
        current_y += self.draw_header(c, current_y, 
                                      "%s (%s)" % (self.report.wetmill.name, self.report.wetmill.country.name), 
                                      _("%s Transparency Sheet") % self.report.season.name if self.report_mode != 'CR'
                                        else _("%s Credit Report") % self.report.season.name)

        current_y += self.SECTION_MARGIN

        # draw our tns logo
        left_height = self.draw_wetmill_attributes(c, current_y)
        right_height = 0

        current_y += max(left_height, right_height)
        current_y += self.SECTION_MARGIN

        # historical performance
        if self.report_mode == 'CR':
            current_y += self.draw_historical_performance(c, current_y)
            current_y += self.SECTION_MARGIN

        # draw our production boxes
        left_height = self.draw_production_boxes(c, current_y)
        right_height = self.draw_sales_box(c, current_y)

        if self.report.season.has_local_sales:
            right_height += self.SECTION_MARGIN
            right_height += self.draw_local_sales_box(c, current_y + right_height)

        right_height += self.SECTION_MARGIN
        right_height += self.draw_working_capital(c, current_y + right_height)


        current_y += max(left_height, right_height) + self.SECTION_MARGIN

        # draw our expenses
        current_y += self.draw_expenses(c, current_y)

        print 'The report mode is: ' + self.report_mode

        # use of cash
        if self.report_mode != 'CR':
            current_y += self.draw_cash_box(c, current_y)
            current_y += self.SECTION_MARGIN

        # farmer box
        if self.report_mode != 'CR':
            current_y += self.draw_farmer_box(c, current_y) + self.SECTION_MARGIN

        self.draw_generated_on(c, current_y)        

    def get_average(self, key):
        if self.aggs and key in self.aggs:
            value = self.aggs[key]
            return value.average
        else:
            return None

    def draw_page_two(self, c):
        # start the second page
        c.showPage()
        current_x = self.PAGE_MARGIN 
        current_y = self.PAGE_MARGIN * 3

        # farmer payment gauge
        farmer_x = current_x
        farmer_y = current_y
        left = self.draw_farmer_payment_gauge(c, current_x, current_y)

        current_x += self.FARMER_PAYMENT_BOX_WIDTH + self.PAGE_MARGIN

        location_x = current_x
        location_y = current_y
        right = self.draw_wetmill_location(c, current_x, current_y)

        height = max(left, right)
        current_y += height

        #draw the boxes around farmer and location sections
        #depending on the max height amongst both sections
        c.rect(farmer_x, farmer_y, self.FARMER_PAYMENT_BOX_WIDTH, height)
        c.rect(location_x, location_y, self.FARMER_PAYMENT_BOX_WIDTH, height)

        current_x = self.PAGE_MARGIN
        current_y += self.PAGE_MARGIN
        current_y += self.draw_performance_dashboard(c, current_x, current_y)

        current_x = self.PAGE_MARGIN
        current_y += self.PAGE_MARGIN
        graph_y = current_y

        self.draw_bar_graph(c, current_x, graph_y, 0, 
                            self.production.cherry_to_parchment_ratio, 
                            self.get_average('cherry_to_parchment_ratio'),
                            _("Cherry to Parchment Ratio"))

        current_x += self.BARGRAPH_BOX_HEADER_WIDTH + self.PAGE_MARGIN
        self.draw_bar_graph(c, current_x, graph_y, 0, 
                            self.production.parchment_to_green_ratio,
                            self.get_average('parchment_to_green_ratio'),
                            _("Parchment to Green Ratio"))

        if self.production.has_top_grade:
            current_x += self.BARGRAPH_BOX_HEADER_WIDTH + self.PAGE_MARGIN
            current_y = self.draw_bar_graph(c, current_x, graph_y, 0, 
                                            self.production.top_grade_percentage,
                                            self.get_average('top_grade_percentage'), 
                                            _("Proportion for Top Grade"), percentage=True) + graph_y
        else:
            current_x += self.BARGRAPH_BOX_HEADER_WIDTH + self.PAGE_MARGIN
            current_y = self.draw_bar_graph(c, current_x, graph_y, 0, 
                                            self.production.cherry_to_green_ratio,
                                            self.get_average('cherry_to_green_ratio'), 
                                            _("Cherry to Green Ratio")) + graph_y
            

        current_x = self.PAGE_MARGIN
        current_y += self.PAGE_MARGIN

        wetmill_values = []
        tns_values = []
        legend = []

        categories = self.expenses.get_categories()
        if categories:
            category = categories[0]
            if category.expense.collapse:
                wetmill_values.append(self.per_weight_unit_green(category.value.as_local(self.exchange)))
                tns_values.append(self.get_average(category.slug()))
                legend.append(category.name)

            else:
                for row in category.children:
                    if not row.expense.is_advance:
                        wetmill_values.append(self.per_weight_unit_green(row.value.as_local(self.exchange)))
                        tns_values.append(self.get_average(row.slug()))                        
                        legend.append(row.name)

        current_y += self.draw_stacked_bar_graph(c, current_x, current_y, 0, 
                                                 wetmill_values, tns_values, 
                                                 _("Coffee Washing Station Expenses (US$/%s Green)") % self.weight_abbreviation, legend)

        current_y += self.PAGE_MARGIN
        self.draw_generated_on(c, current_y)        

    def render(self, output_buffer):
        # Create the PDF object, using the StringIO object as its "file."
        c = self.create_canvas(output_buffer)

        self.draw_page_one(c)

        # only draw the graphs if they are requested
        if self.show_graphs and self.report.is_finalized and self.report.season.is_finalized and self.report_mode != 'CR':
            self.draw_page_two(c)

        c.save()

        return output_buffer
