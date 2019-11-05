from tns_glass.reports.pdf.render import PDFReport
from .base import PDFTestCase
from decimal import Decimal

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class RenderTest(PDFTestCase):

    def setUp(self):
        super(RenderTest, self).setUp()
        self.currency = self.usd

    def render_report(self, show_buyers=True):
        test_buffer = StringIO()
        pdf_report = PDFReport(self.report, self.currency, show_buyers=show_buyers)
        pdf_report.render(test_buffer)

        tmp_file = open('/tmp/report.pdf', 'w')
        tmp_file.write(test_buffer.getvalue())
        tmp_file.close()

    def test_partial_render_no_production(self):
        self.add_grades()
        self.add_sales()
        self.add_expenses()

        self.render_report()

    def test_partial_render_no_sales(self):
        self.add_grades()
        self.add_expenses()

        self.render_report()

    def test_partial_render_no_expense_entries(self):
        self.add_grades()
        self.add_expenses()

        self.report.expenses.all().delete()

        self.render_report()

    def test_full_render(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

        self.render_report()

    def test_full_render_no_members(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.rwanda_2010.has_members = False
        self.rwanda_2010.save()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

        self.render_report()

    def test_full_render_rwf(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

        self.currency = self.rwf

        self.render_report()

    def test_gauge_render(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

        test_buffer = StringIO()
        pdf_report = PDFReport(self.report, self.currency)

        # create the canvas
        c = pdf_report.create_canvas(test_buffer)

        # test wrap_word
        # with text containing space
        label = "Hello, world"
        pdf_report.wrap_word(c, 0, 0, 100, "left", label)

        # with text without spacing
        label = "blablafoobarbarfoobarfoooooooofoobar"
        pdf_report.wrap_word(c, 0, 0, 100, "left", label)

        # with long text but short length thus 
        label = "bla blasdlskdfjlaskdjf"
        pdf_report.wrap_word(c, 0, 0, 20, "right", label)

        # with text as none
        label = None
        pdf_report.wrap_word(c, 0, 0, 100, "left", label)

        # test gauge rotation method
        # with minimum less than maximum
        pdf_report.gauge_rotation(0,100,86)
        # with minimun greater than maximum
        pdf_report.gauge_rotation(100,0,86)
        # with current value out of min max range
        pdf_report.gauge_rotation(10,100,6)
        pdf_report.gauge_rotation(10,100,110)
        # with equal min max
        pdf_report.gauge_rotation(0,0,0)

        # test draw gauge
        # with one null value between minimum, maximum and current value
        pdf_report.draw_gauge(c,0,0,100,None,0,0,"Hello",9,7)

        # using one country object, will change the name
        # for Rwanda
        pdf_report.lat_to_x(self.rwanda, 1.25458)
        pdf_report.lng_to_y(self.rwanda, 30.25458)

        pdf_report.draw_country_map(c, 0,0,100,self.rwanda, 1.25458, 30.25458)

        pdf_report.report.season.country = self.rwanda
        pdf_report.draw_wetmill_location(c, 0,0)

        # for Kenya
        self.rwanda.name = "Kenya"
        pdf_report.lat_to_x(self.rwanda, 1.25458)
        pdf_report.lng_to_y(self.rwanda, 30.25458)

        pdf_report.draw_country_map(c, 0,0,100,self.rwanda, 1.25458, 30.25458)

        pdf_report.report.season.country = self.rwanda
        pdf_report.draw_wetmill_location(c, 0,0)

        # for Ethiopia
        self.rwanda.name = "Ethiopia"
        pdf_report.lat_to_x(self.rwanda, 1.25458)
        pdf_report.lng_to_y(self.rwanda, 30.25458)

        pdf_report.draw_country_map(c, 0,0,100,self.rwanda, 1.25458, 30.25458)

        pdf_report.report.season.country = self.rwanda
        pdf_report.draw_wetmill_location(c, 0,0)

        # for Tanzania
        self.rwanda.name = "Tanzania"
        pdf_report.lat_to_x(self.rwanda, 1.25458)
        pdf_report.lng_to_y(self.rwanda, 30.25458)

        pdf_report.draw_country_map(c, 0, 0, 100,self.rwanda, 1.25458, 30.25458)

        pdf_report.report.season.country = self.rwanda
        pdf_report.draw_wetmill_location(c, 0, 0)

        # test nice number method
        pdf_report.nice_number(-1, True)
        pdf_report.nice_number(-1, False)
        pdf_report.nice_number(.9, True)
        pdf_report.nice_number(.9, False)
        pdf_report.nice_number(.01, False)

        # test draw y axis
        pdf_report.draw_yaxis(c, 0,0,100,30,0,0,10,True,None)

        # test draw bar chart value method
        pdf_report.draw_bar_value(c, 100, 20, 12, Decimal(25))

        # test draw bar graph method with min, max and value as null
        pdf_report.draw_bar_graph(c, 0, 0, None, None, None, "Something")

        # test draw stacked bar graph with most of values as null
        legend_titles = ["One", "Two", "Three", "Four"]

        wetmill_values = [None, None, None, None]
        tns_values = [None, None, None, None]
        pdf_report.draw_stacked_bar_graph(c, 0, 0, None, wetmill_values, tns_values,  "Some title", legend_titles)

        # test draw stacked bar graph with normal values
        wetmill_values = [Decimal(".5"), Decimal(".32"), Decimal(".12"), Decimal(".58")]
        tns_values = [Decimal(".1"), Decimal(".56"), Decimal(".5"), Decimal(".9")]
        pdf_report.draw_stacked_bar_graph(c, 0, 0, 1.5, wetmill_values, tns_values, "Some other title", legend_titles, percentage=True)

    def test_full_render_with_aggregates(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.capacity = Decimal("20000")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.is_finalized = True
        self.report.save()

        self.currency = self.usd

        from aggregates.models import SeasonAggregate
        self.assertEquals(1, SeasonAggregate.calculate_for_season(self.report.season))

        self.render_report()

    def test_full_render_with_aggregates_no_top(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        # this will make green 15 not a top grade
        self.rwanda_2010.add_grade(self.green15, False)

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.capacity = Decimal("20000")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.is_finalized = True
        self.report.save()

        self.currency = self.usd

        from aggregates.models import SeasonAggregate
        self.assertEquals(1, SeasonAggregate.calculate_for_season(self.report.season))

        self.render_report()

    def test_full_render_with_collapsed_wetmill_expenses(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        # this will set the washing station expenses as collapsed
        self.rwanda_2010.add_expense(self.washing_expenses, True)

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.capacity = Decimal("20000")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.is_finalized = True
        self.report.save()

        self.currency = self.usd

        from aggregates.models import SeasonAggregate
        self.assertEquals(1, SeasonAggregate.calculate_for_season(self.report.season))

        self.render_report()

    def test_full_render_rwf(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.capacity = Decimal("20000")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.is_finalized = True
        self.report.save()

        self.currency = self.rwf

        from aggregates.models import SeasonAggregate
        self.assertEquals(1, SeasonAggregate.calculate_for_season(self.report.season))

        self.render_report()

    def test_full_render_finalized_no_aggs(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.capacity = Decimal("20000")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.is_finalized = True
        self.report.save()

        self.currency = self.rwf

        from aggregates.models import SeasonAggregate
        self.assertEquals(1, SeasonAggregate.calculate_for_season(self.report.season))
        SeasonAggregate.objects.all().delete()

        self.render_report()

    def test_full_render_collapse_washing(self):
        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.rwanda_2010.add_expense(self.washing_expenses, True)

        self.report.working_capital = Decimal("11407500")
        self.report.working_capital_repaid = Decimal("128700")
        self.report.miscellaneous_sources = Decimal("0")
        self.report.save()

        self.render_report()

    def test_full_render_ethiopia(self):
        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
        self.add_ethiopia_expenses()
        self.add_ethiopia_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.render_report()

    def test_full_render_ethiopia_hide_buyers(self):
        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
        self.add_ethiopia_expenses()
        self.add_ethiopia_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.render_report(show_buyers=False)

    def test_full_render_misc_revenue(self):
        self.season.has_misc_revenue = True
        self.season.save()

        self.report.miscellaneous_revenue = Decimal("100000")
        self.report.save()

        self.add_grades()
        self.add_productions()
        self.add_sales()
        self.add_expenses()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        self.render_report()

    def test_render_wrap(self):
        self.add_grades()
        self.add_expenses()

        self.green15.name = "A long grade name that will be forced to wrap"
        self.green15.save()

        self.washing_expenses.name = "This is a really long expense name that will be forced to wrap but man it really needs to be crazy long and needing to be wrapped"
        self.washing_expenses.save()

        self.cherry_advance.name = "CherryAdvanceIsAllOneReallyLongWordWithoutSpacesWhatWillHappenIfitcontinuestobesocrazylongOhMyWhatWillHappen"
        self.cherry_advance.save()

        self.render_report()


    def test_round_value(self):
        test_buffer = StringIO()
        pdf_report = PDFReport(self.report, self.currency)

        self.assertEquals("100.12", pdf_report.round_value(Decimal("100.1203")))
        self.assertEquals("100.13", pdf_report.round_value(Decimal("100.1293")))

        self.assertEquals("None", pdf_report.round_value(None))
        self.assertEquals("1.3", pdf_report.round_value("1.3"))





