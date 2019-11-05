from ..models import *
from reports.pdf.production import *
from .base import PDFTestCase
from datetime import datetime
from decimal import Decimal
from seasons.models import SeasonGrade

class ProductionTest(PDFTestCase):

    def setUp(self):
        super(ProductionTest, self).setUp()
        self.season = self.rwanda_2010
        self.add_grades()
        self.add_productions()

    def test_ethiopia_box(self):
        self.setup_ethiopia_season()
        self.add_ethiopia_productions()
        box = ProductionBox(self.report)

        categories = box.get_categories()
        self.assertEquals(4, len(categories))

        self.assertEquals("Cherry", categories[0].name)
        self.assertEquals(Decimal("54991"), categories[0].volume)
        rows = categories[0].rows
        self.assertEquals(2, len(rows))
        self.assertEquals("Washed", rows[0].name)
        self.assertEquals(Decimal("54788"), rows[0].volume)
        self.assertEquals("Converted to natural", rows[1].name)
        self.assertEquals(Decimal("203"), rows[1].volume)

        self.assertEquals("Parchment", categories[1].name)
        self.assertEquals(Decimal("10244"), categories[1].volume)

        rows = categories[1].rows
        self.assertEquals(2, len(rows))
        self.assertEquals("Dry-milled", rows[0].name)
        self.assertEquals(Decimal("9855"), rows[0].volume)
        self.assertEquals("Sold locally", rows[1].name)
        self.assertEquals(Decimal("389"), rows[1].volume)    

        self.assertEquals("Jenfel", categories[2].name)
        self.assertEquals(Decimal("68"), categories[2].volume)

        rows = categories[2].rows
        self.assertEquals(2, len(rows))
        self.assertEquals("Dry-milled", rows[0].name)
        self.assertEquals(Decimal("68"), rows[0].volume)
        self.assertEquals("Sold locally", rows[1].name)
        self.assertEquals(Decimal("0"), rows[1].volume)    

        self.assertEquals("Green", categories[3].name)
        self.assertEquals(Decimal("8213"), categories[3].volume)

        rows = categories[3].rows
        self.assertEquals(2, len(rows))
        self.assertEquals("Washed", rows[0].name)
        self.assertEquals(Decimal("8187"), rows[0].volume)
        self.assertEquals(Decimal("100"), rows[0].percent)

        self.assertEquals("Naturals", rows[1].name)
        self.assertEquals(Decimal("26"), rows[1].volume)
        self.assertEquals(Decimal("0"), rows[1].percent)

        self.assertFalse(box.has_top_grade)
        self.assertDecimalEquals(Decimal("8187"), box.top_grade_total)
        self.assertDecimalEquals(Decimal("6.69"), box.cherry_to_top_grade_ratio)
        self.assertIsNone(box.top_grade_percentage)

        self.assertDecimalEquals(Decimal("5.35"), box.cherry_to_parchment_ratio)
        self.assertDecimalEquals(Decimal("1.20"), box.parchment_to_green_ratio)
        self.assertDecimalEquals(Decimal("6.44"), box.cherry_to_green_ratio)

    def test_production_box(self):
        self.report.capacity = Decimal("20000")
        self.report.save()

        box = ProductionBox(self.report)

        categories = box.get_categories()
        self.assertEquals(3, len(categories))

        self.assertEquals("Cherry", categories[0].name)
        self.assertEquals(Decimal("68654"), categories[0].volume)
        self.assertEquals(0, len(categories[0].rows))

        self.assertEquals("Parchment", categories[1].name)
        self.assertEquals(Decimal("13723"), categories[1].volume)
        self.assertEquals(0, len(categories[1].rows))

        self.assertEquals("Green", categories[2].name)
        self.assertEquals(Decimal("11035"), categories[2].volume)

        self.assertDecimalEquals("69", box.utilization)

        self.assertTrue(box.has_top_grade)
        self.assertDecimalEquals(Decimal("8880"), box.top_grade_total)
        self.assertDecimalEquals(Decimal("7.73"), box.cherry_to_top_grade_ratio)
        self.assertDecimalEquals(Decimal("80"), box.top_grade_percentage)

        rows = categories[2].rows
        self.assertEquals(3, len(categories[2].rows))
        self.assertEquals("Screen 15+", rows[0].name)
        self.assertEquals(Decimal("8880"), rows[0].volume)
        self.assertEquals(Decimal("80"), rows[0].percent)

        self.assertEquals("Screen 13,14", rows[1].name)
        self.assertEquals(Decimal("1092"), rows[1].volume)
        self.assertEquals(Decimal("10"), rows[1].percent)

        self.assertEquals("Low Grades", rows[2].name)
        self.assertEquals(Decimal("1063"), rows[2].volume)
        self.assertEquals(Decimal("10"), rows[2].percent)

        self.assertDecimalEquals(Decimal("5.00"), box.cherry_to_parchment_ratio)
        self.assertDecimalEquals(Decimal("1.24"), box.parchment_to_green_ratio)
        self.assertDecimalEquals(Decimal("6.22"), box.cherry_to_green_ratio)


