from decimal import Decimal

ZERO = Decimal("0")

class CurrencyValue(object):
    """
    A CurrencyValue represents a Decimal value along with an optional exchange rate.

    It allows for easy addition and substraction of values while maintaining the original currency, the 
    final value only calculated at the very last minute.

    It also takes care of ignoring values which are None.
    """
    def __init__(self, value=None, exchange=None):
        """
        Creates a new value.  If an exchange rate is passed in, then the value is assumed to be in 
        US dollars and that exchange will be used when convering to a local currency.
        """
        self.usd_values = []

        if isinstance(value, CurrencyValue):
            if exchange is None:
                self.local_value = value.local_value
                self.usd_values = value.usd_values
                return
            else:
                raise Exception("Invalid arguments to constructor, passing in CurrencyValue and exchange rate")

        # if we don't have an exchange rate, our value is in local currency, just save it away
        if exchange is None:
            self.local_value = value

        # otherwise, this is a usd value
        else:
            self.local_value = None
            
            # so add this value / exchange pair to our list of usd values
            if not value is None:
                self.usd_values.append([value, exchange])

    def forex_loss(self, exchange):
        """
        Calculates our total forex loss.. 
        """
        loss = Decimal("0")

        for usd_value in self.usd_values:
            loss -= usd_value[0] * (usd_value[1] - exchange)

        return CurrencyValue(loss)

    def as_local(self, exchange):
        # no local or usd values?  then return None
        if self.local_value is None and not self.usd_values:
            return None

        # first add in our local value
        if self.local_value:
            local = self.local_value
        else:
            local = Decimal("0")

        # then for each of our usd values, calculate our total
        for usd_value in self.usd_values:
            local += usd_value[0] * exchange

        return local

    def as_usd(self, exchange):
        if exchange is None:
            raise Exception("Must specify an exchange rate when getting the value as USD")

        # no local or usd values?  then return None
        if self.local_value is None and not self.usd_values:
            return None

        # convert any local value to USD using the passed in exchange
        if self.local_value:
            usd = self.local_value / exchange
        else:
            usd = Decimal("0")

        # add up all our local usd values
        for usd_value in self.usd_values:
            usd += usd_value[0]

        return usd

    def negate(self):
        local_value = None
        if self.local_value:
            local_value = self.local_value * Decimal("-1")

        negated = CurrencyValue(local_value)

        for usd_value in self.usd_values:
            negated.usd_values.append([usd_value[0] * Decimal("-1"), usd_value[1]])

        return negated

    @classmethod
    def add(cls, left, right):
        if right is None and not left is None:
            return left

        # both are not none at this point
        local_total = left.local_value

        if not right.local_value is None:
            if local_total is None:
                local_total = right.local_value
            else:
                local_total += right.local_value

        # our usd values
        usd_values = []
        
        for usd_value in left.usd_values:
            usd_values.append(usd_value)

        for usd_value in right.usd_values:
            usd_values.append(usd_value)

        combined = CurrencyValue(local_total)
        for usd_value in usd_values:
            combined.usd_values.append(usd_value)

        return combined

    @classmethod
    def sub(cls, left, right):
        if left is None and right:
            return right.negate()

        if left and right is None:
            return left

        return left + right.negate()

    @classmethod
    def mul(cls, left, right):
        if left is None or right is None:
            return None

        if not isinstance(left, Decimal) and not isinstance(right, Decimal):
            raise Exception("CurrencyValue objects can only be multiplied by Decimal objects")

        if isinstance(right, Decimal):
            dec = right
            cv = left
        else:
            raise Exception("Multiplication of CurrencyValue objects is only supposed with Decimal objects") # pragma: no cover
        
        combined = CurrencyValue(cv.local_value)
        if cv.local_value:
            combined.local_value = cv.local_value * dec

        for usd_value in cv.usd_values:
            combined.usd_values.append([usd_value[0] * dec, usd_value[1]])

        return combined

    @classmethod
    def div(cls, left, right):
        global ZERO

        if left is None or right is None:
            return None

        if not isinstance(left, CurrencyValue) or not isinstance(right, Decimal):
            raise Exception("Division only supported as CurrencyValue / Decimal")

        if right == ZERO:
            return CurrencyValue(ZERO)

        combined = CurrencyValue(left.local_value)
        if left.local_value:
            combined.local_value = left.local_value / right

        for usd_value in left.usd_values:
            combined.usd_values.append([usd_value[0] / right, usd_value[1]])

        return combined

    def __str__(self):
        as_str = "%s - [" % self.local_value
        as_str += ", ".join(["%d (%d)" % (usd[0], usd[1]) for usd in self.usd_values])
        as_str += "]"
        return as_str
        
    # operator overloading
    def __add__(self, other):
        return CurrencyValue.add(self, other)

    def __radd__(self, other):
        return CurrencyValue.add(self, other)

    def __iadd__(self, other):
        return CurrencyValue.add(self, other)

    def __sub__(self, other):
        return CurrencyValue.sub(self, other)

    def __rsub__(self, other):
        return CurrencyValue.sub(other, self)

    def __isub__(self, other):
        return CurrencyValue.sub(self, other)

    def __mul__(self, other):
        return CurrencyValue.mul(self, other)

    def __rmul__(self, other):
        return CurrencyValue.mul(self, other)

    def __imul__(self, other):
        return CurrencyValue.mul(self, other)

    def __div__(self, other):
        return CurrencyValue.div(self, other)

    def __rdiv__(self, other):
        return CurrencyValue.div(other, self)

    def __idiv__(self, other):
        return CurrencyValue.div(self, other)

CV_ZERO = CurrencyValue(Decimal("0"))


    


        


        
            
            
            



    
