from ..models import *
from reports.pdf.sales import *
from .base import PDFTestCase
from datetime import datetime
from decimal import Decimal

class SalesTest(PDFTestCase):

    def setUp(self):
        super(SalesTest, self).setUp()
        self.add_grades()
        self.add_sales()

    def test_sales_box_usd(self):
        # generate our sales box
        box = SalesBox(self.report, self.usd)

        rows = box.get_export_rows()
        self.assertEquals(5, len(rows))

        ex = self.rwanda_2010.exchange_rate

        self.assertEquals("Rogers Family Co.", rows[0].buyer)
        self.assertEquals("FOT", rows[0].sale_type)
        self.assertEquals("Green - Screen 15+", rows[0].grade_string())
        self.assertDecimalEquals(Decimal("660"), rows[0].volume)
        self.assertDecimalEquals(Decimal("3.60"), rows[0].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.76"), rows[0].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("2481.60"), rows[0].revenue.as_usd(ex))

        self.assertEquals("Rogers Family Co.", rows[1].buyer)
        self.assertEquals("FOT", rows[1].sale_type)
        self.assertEquals("Green - Screen 15+", rows[1].grade_string())
        self.assertDecimalEquals(Decimal("8220"), rows[1].volume)
        self.assertDecimalEquals(Decimal("3.60"), rows[1].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.76"), rows[1].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("30907.20"), rows[1].revenue.as_usd(ex))

        self.assertEquals("Rwacof", rows[2].buyer)
        self.assertEquals("FOT", rows[2].sale_type)
        self.assertEquals("Green - Screen 13,14", rows[2].grade_string())
        self.assertDecimalEquals(Decimal("1092"), rows[2].volume)
        self.assertDecimalEquals(Decimal("3.31"), rows[2].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.47"), rows[2].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3787.62"), rows[2].revenue.as_usd(ex))

        self.assertEquals("Rwacof", rows[3].buyer)
        self.assertEquals("FOT", rows[3].sale_type)
        self.assertEquals("Green - Low Grades", rows[3].grade_string())
        self.assertDecimalEquals(Decimal("1063"), rows[3].volume)
        self.assertDecimalEquals(Decimal("1.06"), rows[3].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("1.22"), rows[3].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("1300.69"), rows[3].revenue.as_usd(ex))

        total_row = rows[-1]

        self.assertTrue(total_row.is_total)
        self.assertDecimalEquals(Decimal("11035"), total_row.volume)
        self.assertDecimalEquals(Decimal("3.33"), total_row.fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.49"), total_row.fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("38477.11"), total_row.revenue.as_usd(ex))

        self.assertDecimalEquals("1765.60", box.total_freight.as_usd(ex))
        self.assertDecimalEquals("-212.44", box.total_revenue.forex_loss(ex).as_usd(ex))
        self.assertDecimalEquals("3.33", box.fot_price.as_usd(ex))

        self.assertEquals(1, len(box.get_local_rows()))

    def test_negative_price(self):
        sale = self.report.sales.all()[0]
        sale.price = Decimal("0")
        sale.save()

        box = SalesBox(self.report, self.usd)
        rows = box.get_export_rows()

        ex = Decimal("585")
        self.assertDecimalEquals(Decimal("0"), rows[0].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("0"), rows[0].fob_price.as_local(ex))

        sale = self.report.sales.all()[0]
        sale.sale_type = 'FOB'
        sale.save()

        box = SalesBox(self.report, self.usd)
        rows = box.get_export_rows()

        ex = Decimal("585")
        self.assertDecimalEquals(Decimal("0"), rows[0].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("0"), rows[0].fob_price.as_local(ex))

    def test_sales_no_combine(self):
        # change one of our sales to FOB
        rwacof_sale = self.report.sales.all()[6]
        rwacof_sale.components.all().delete()

        # create a new depth 2 grade under 15+
        green15sub = self.add_grade("Green 15 Sub", "GRE", 3, self.green15)        
        self.rwanda_2010.add_grade(green15sub)        

        rwacof_sale.components.create(grade=green15sub, volume=170, created_by=self.admin, modified_by=self.admin)
        rwacof_sale.components.create(grade=self.hpc, volume=3, created_by=self.admin, modified_by=self.admin)

        # generate our sales box
        box = SalesBox(self.report, self.usd)

        rows = box.get_export_rows()

        # should have five rows, we weren't able to combine the modified rwacof sale with the others
        # since it has a different depth 1 parent
        self.assertEquals(6, len(rows))

    def test_sales_box_fob(self):
        # change one of our sales to FOB
        rogers_sale = self.report.sales.all()[0]
        rogers_sale.sale_type = 'FOB'
        rogers_sale.save()

        # generate our sales box
        box = SalesBox(self.report, self.usd)

        rows = box.get_export_rows()
        ex = Decimal("585")

        self.assertEquals("Rogers Family Co.", rows[0].buyer)
        self.assertEquals("FOB", rows[0].sale_type)
        self.assertEquals("Green - Screen 15+", rows[0].grade_string())
        self.assertDecimalEquals(Decimal("660"), rows[0].volume)
        self.assertDecimalEquals(Decimal("3.44"), rows[0].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.60"), rows[0].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("2376.00"), rows[0].revenue.as_usd(ex))

        self.assertEquals("Rogers Family Co.", rows[1].buyer)
        self.assertEquals("FOT", rows[1].sale_type)
        self.assertEquals("Green - Screen 15+", rows[1].grade_string())
        self.assertDecimalEquals(Decimal("8220"), rows[1].volume)
        self.assertDecimalEquals(Decimal("3.60"), rows[1].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.76"), rows[1].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("30907.20"), rows[1].revenue.as_usd(ex))

        self.assertEquals("Rwacof", rows[2].buyer)
        self.assertEquals("FOT", rows[2].sale_type)
        self.assertEquals("Green - Screen 13,14", rows[2].grade_string())
        self.assertDecimalEquals(Decimal("1092"), rows[2].volume)
        self.assertDecimalEquals(Decimal("3.31"), rows[2].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.47"), rows[2].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3787.62"), rows[2].revenue.as_usd(ex))

        self.assertEquals("Rwacof", rows[3].buyer)
        self.assertEquals("FOT", rows[3].sale_type)
        self.assertEquals("Green - Low Grades", rows[3].grade_string())
        self.assertDecimalEquals(Decimal("1063"), rows[3].volume)
        self.assertDecimalEquals(Decimal("1.06"), rows[3].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("1.22"), rows[3].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("1300.69"), rows[3].revenue.as_usd(ex))

        total_row = rows[-1]

        self.assertTrue(total_row.is_total)
        self.assertDecimalEquals(Decimal("11035"), total_row.volume)
        self.assertDecimalEquals(Decimal("3.32"), total_row.fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("3.48"), total_row.fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("38371.51"), total_row.revenue.as_usd(ex))

        self.assertDecimalEquals("1660.00", box.total_freight.as_usd(ex))
        self.assertDecimalEquals("-124279.92", box.total_revenue.forex_loss(ex).as_local(ex))

        self.assertEquals(1, len(box.get_local_rows()))

    def test_sales_box_rwf(self):
        # generate our sales box
        box = SalesBox(self.report, self.rwf)

        rows = box.get_export_rows()
        self.assertEquals(5, len(rows))

        ex = self.rwanda_2010.exchange_rate

        self.assertEquals("Rogers Family Co.", rows[0].buyer)
        self.assertEquals("FOT", rows[0].sale_type)
        self.assertEquals("Green - Screen 15+", rows[0].grade_string())
        self.assertDecimalEquals(Decimal("660"), rows[0].volume)
        self.assertDecimalEquals(Decimal("2106.00"), rows[0].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("2199.60"), rows[0].fob_price.as_local(ex))
        self.assertDecimalEquals(Decimal("1451736.00"), rows[0].revenue.as_local(ex))

        self.assertEquals("Rogers Family Co.", rows[1].buyer)
        self.assertEquals("FOT", rows[1].sale_type)
        self.assertEquals("Green - Screen 15+", rows[1].grade_string())
        self.assertDecimalEquals(Decimal("8220"), rows[1].volume)
        self.assertDecimalEquals(Decimal("2106.00"), rows[1].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("2199.60"), rows[1].fob_price.as_local(ex))
        self.assertDecimalEquals(Decimal("18080712.00"), rows[1].revenue.as_local(ex))

        self.assertEquals("Rwacof", rows[2].buyer)
        self.assertEquals("FOT", rows[2].sale_type)
        self.assertEquals("Green - Screen 13,14", rows[2].grade_string())
        self.assertDecimalEquals(Decimal("1092"), rows[2].volume)
        self.assertDecimalEquals(Decimal("1935.48"), rows[2].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("2029.08"), rows[2].fob_price.as_local(ex))
        self.assertDecimalEquals(Decimal("2215755.36"), rows[2].revenue.as_local(ex))

        self.assertEquals("Rwacof", rows[3].buyer)
        self.assertEquals("FOT", rows[3].sale_type)
        self.assertEquals("Green - Low Grades", rows[3].grade_string())
        self.assertDecimalEquals(Decimal("1063"), rows[3].volume)
        self.assertDecimalEquals(Decimal("622.21"), rows[3].fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("715.81"), rows[3].fob_price.as_local(ex))
        self.assertDecimalEquals(Decimal("760904.57"), rows[3].revenue.as_local(ex))

        total_row = rows[-1]

        self.assertTrue(total_row.is_total)
        self.assertDecimalEquals(Decimal("11035"), total_row.volume)
        self.assertDecimalEquals(Decimal("1946.19"), total_row.fot_price.as_local(ex))
        self.assertDecimalEquals(Decimal("2039.79"), total_row.fob_price.as_local(ex))
        self.assertDecimalEquals(Decimal("22509107.93"), total_row.revenue.as_local(ex))

        self.assertDecimalEquals("1032876.00", box.total_freight.as_local(ex))
        self.assertDecimalEquals("-124279.92", box.total_revenue.forex_loss(self.report.season.exchange_rate).as_local(ex))

        self.assertEquals(1, len(box.get_local_rows()))

class EthiopiaSalesTest(PDFTestCase):

    def setUp(self):
        super(EthiopiaSalesTest, self).setUp()
        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        self.add_ethiopia_sales()
    
    def test_ethiopia_sales(self):
        # generate our sales box
        box = SalesBox(self.report, self.usd)

        rows = box.get_export_rows()
        self.assertEquals(2, len(rows))

        ex = self.rwanda_2010.exchange_rate

        self.assertEquals("Buyer A", rows[0].buyer)
        self.assertEquals("FOB", rows[0].sale_type)
        self.assertEquals("Green - Washed", rows[0].grade_string())
        self.assertDecimalEquals(Decimal("7058"), rows[0].volume)
        self.assertDecimalEquals(Decimal("3.94"), rows[0].fot_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("4.14"), rows[0].fob_price.as_usd(ex))
        self.assertDecimalEquals(Decimal("29254"), rows[0].revenue.as_usd(ex))

        rows = box.get_local_rows()
        self.assertEquals(5, len(rows))
        
        ex = self.rwanda_2010.exchange_rate

        self.assertEquals("Buyer B", rows[0].buyer)
        self.assertEquals("LOC", rows[0].sale_type)
        self.assertEquals("Green - Washed", rows[0].grade_string())
        self.assertDecimalEquals(Decimal("1129"), rows[0].volume)
        self.assertDecimalEquals(Decimal("1.86"), rows[0].price.as_usd(ex))
        self.assertDecimalEquals(Decimal("2102.54"), rows[0].revenue.as_usd(ex))

        self.assertEquals("Buyer C", rows[1].buyer)
        self.assertEquals("LOC", rows[1].sale_type)
        self.assertEquals("Parchment - Sold locally", rows[1].grade_string())
        self.assertDecimalEquals(Decimal("300"), rows[1].volume)
        self.assertDecimalEquals(Decimal("1.20"), rows[1].price.as_usd(ex))
        self.assertDecimalEquals(Decimal("360"), rows[1].revenue.as_usd(ex))

        self.assertEquals("Buyer D", rows[2].buyer)
        self.assertEquals("LOC", rows[2].sale_type)
        self.assertEquals("Parchment - Sold locally", rows[2].grade_string())
        self.assertDecimalEquals(Decimal("89"), rows[2].volume)
        self.assertDecimalEquals(Decimal("1.00"), rows[2].price.as_usd(ex))
        self.assertDecimalEquals(Decimal("89"), rows[2].revenue.as_usd(ex))

        self.assertEquals("Buyer E", rows[3].buyer)
        self.assertEquals("LOC", rows[3].sale_type)
        self.assertEquals("Green - Naturals", rows[3].grade_string())
        self.assertDecimalEquals(Decimal("26"), rows[3].volume)
        self.assertDecimalEquals(Decimal("2.46"), rows[3].price.as_usd(ex))
        self.assertDecimalEquals(Decimal("63.97"), rows[3].revenue.as_usd(ex))

        self.assertEquals("Total Sales", rows[4].buyer)
        self.assertDecimalEquals(Decimal("1544"), rows[4].volume)
        self.assertDecimalEquals(Decimal("1.69"), rows[4].price.as_usd(ex))
        self.assertDecimalEquals(Decimal("2615.51"), rows[4].revenue.as_usd(ex))

        self.assertDecimalEquals("31869.51", box.total_revenue.as_usd(ex))
        self.assertDecimalEquals("0", box.total_freight.as_usd(ex))
        
