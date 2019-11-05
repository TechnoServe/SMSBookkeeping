from django.test import TestCase
from reports.pdf.currencyvalue import CurrencyValue as CV
from decimal import Decimal

class CurrencyValueTestCase(TestCase):

    def test_nones(self):
        val = CV(None)
        self.assertIsNone(val.as_local(Decimal("585")))
        self.assertIsNone(val.as_usd(Decimal("585")))

        val = CV(None, Decimal("585"))
        self.assertIsNone(val.as_local(Decimal("585")))
        self.assertIsNone(val.as_usd(Decimal("585")))
        
        try:
            val = CV(Decimal("5"))
            val.as_usd(None)
            self.assertFalse(True, "Should have raised exception due to missing exchange rate")
        except:
            pass

    def test_cloning(self):
        val = CV(Decimal("1000"))
        val2 = CV(val)
        self.assertEquals(val.as_local(Decimal("500")), val2.as_local(Decimal("500")))

        try:
            val2 = CV(val, Decimal("500"))
            self.assertFalse(True, "Should have thrown, invalid constructor")
        except:
            pass

    def test_conversion(self):
        val = CV(Decimal("1000"))

        self.assertEquals(Decimal("1000"), val.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), val.as_usd(Decimal("500")))

        self.assertEquals("1000 - []", str(val))

        val = CV(Decimal("2"), Decimal("500"))
        self.assertEquals(Decimal("1000"), val.as_local(Decimal("500")))
        self.assertEquals(Decimal("1200"), val.as_local(Decimal("600")))
        self.assertEquals(Decimal("2"), val.as_usd(Decimal("500")))

        self.assertEquals("None - [2 (500)]", str(val))

    def test_addition(self):
        val = CV(None)
        val2 = CV(None)
        total = val + val2
        
        self.assertIsNone(total.as_local(Decimal("585")))
        self.assertIsNone(total.as_usd(Decimal("585")))

        val = CV(Decimal("1000"))

        total = val + val2

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        total = val2 + val

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        total = None + val

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        total = val + None

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        val = CV(Decimal("1"), Decimal("500"))
        val2 = CV(Decimal("2"), Decimal("250"))

        total = val + val2

        self.assertEquals(Decimal("1500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("3"), total.as_usd(Decimal("500")))

        total += CV(Decimal("1000"))

        self.assertEquals(Decimal("2500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("5"), total.as_usd(Decimal("500")))

        total = total.negate()

        self.assertEquals(Decimal("-2500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-5"), total.as_usd(Decimal("500")))

    def test_subtraction(self):
        val = CV(None)
        val2 = CV(None)
        total = val - val2
        
        self.assertIsNone(total.as_local(Decimal("500")))
        self.assertIsNone(total.as_usd(Decimal("500")))

        val = CV(Decimal("1000"))

        total = val - val2

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        total = val2 - val

        self.assertEquals(Decimal("-1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-2"), total.as_usd(Decimal("500")))

        total = None - val

        self.assertEquals(Decimal("-1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-2"), total.as_usd(Decimal("500")))

        total = val - None

        self.assertEquals(Decimal("1000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("2"), total.as_usd(Decimal("500")))

        val = CV(Decimal("1"), Decimal("500"))
        val2 = CV(Decimal("2"), Decimal("250"))

        total = val - val2

        self.assertEquals(Decimal("-500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-1"), total.as_usd(Decimal("500")))

        total -= CV(Decimal("1000"))

        self.assertEquals(Decimal("-1500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-3"), total.as_usd(Decimal("500")))

    def test_multiplication(self):
        val = CV(None)
        total = val * None
        
        self.assertIsNone(total)
        self.assertIsNone(total)

        total = None * val
        
        self.assertIsNone(total)
        self.assertIsNone(total)

        val = CV(Decimal("1000"))
        total = None * val

        self.assertIsNone(total)
        self.assertIsNone(total)

        total = val * None

        self.assertIsNone(total)
        self.assertIsNone(total)

        total = val * Decimal("2")

        self.assertEquals(Decimal("2000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("4"), total.as_usd(Decimal("500")))

        total = Decimal("2") * val

        self.assertEquals(Decimal("2000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("4"), total.as_usd(Decimal("500")))

        total = val
        total *= Decimal("2")

        self.assertEquals(Decimal("2000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("4"), total.as_usd(Decimal("500")))

        val = CV(Decimal("4"), Decimal("500")) + CV(Decimal("1000"))
        total = Decimal("-2") * val

        self.assertEquals(Decimal("-6000"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-12"), total.as_usd(Decimal("500")))

        # test invalid combinations
        val1 = CV(Decimal("10"))
        val2 = CV(Decimal("20"))
        
        try:
            total = val1 * val2
            self.assertFalse(True, "Should have thrown, invalid operation")
        except:
            pass

    def test_forex_loss(self):
        val = CV(Decimal("50"), Decimal("500"))
        self.assertEquals(Decimal("500"), val.forex_loss(Decimal("510")).as_local(Decimal("500")))

    def test_division(self):
        val = CV(None)
        total = val / None
        
        self.assertIsNone(total)
        self.assertIsNone(total)

        total = None / val
        
        self.assertIsNone(total)
        self.assertIsNone(total)

        val = CV(Decimal("1000"))
        total = None / val

        self.assertIsNone(total)
        self.assertIsNone(total)

        total = val / None

        self.assertIsNone(total)
        self.assertIsNone(total)

        total = val / Decimal("2")

        self.assertEquals(Decimal("500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("1"), total.as_usd(Decimal("500")))

        total = val
        total /= Decimal("2")

        self.assertEquals(Decimal("500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("1"), total.as_usd(Decimal("500")))

        try:
            total = Decimal("2") / val
            self.assertTrue(False, "Should have raised exception as numerator must always be CurrencyValue")
        except Exception as e:
            pass

        val = CV(Decimal("4"), Decimal("500")) + CV(Decimal("1000"))
        total = val / Decimal("-2")

        self.assertEquals(Decimal("-1500"), total.as_local(Decimal("500")))
        self.assertEquals(Decimal("-3"), total.as_usd(Decimal("500")))


    
