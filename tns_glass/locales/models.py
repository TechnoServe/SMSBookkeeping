from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from smartmin.models import SmartModel
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe


def comma_formatted(value, has_decimals, use_comma=True, use_one_decimal_place=False):
    """
    Returns the passed in Decimal as a string, with the appropriate number of decimals
    and commas every three digits.
    """
    formatted = ""
    negative = False

    if value < 0:
        value = -value
        negative = True

    if has_decimals:
        if use_one_decimal_place:
            decimal_portion = (value * 10) % 10
            formatted = ".%d" % decimal_portion
        else:
            decimal_portion = (value * 100) % 100
            formatted = ".%02d" % decimal_portion

    # now do the rest, 1000 at a time
    remainder = int(value)

    while remainder >= 1000:
        if use_comma:
            formatted = (",%03d" % (remainder % 1000)) + formatted
        else:
            formatted = ("%03d" % (remainder % 1000)) + formatted
        remainder = remainder / 1000

    formatted = ("%d" % remainder) + formatted

    # deal with the negative case
    if negative:
        formatted = "-" + formatted
        
    return formatted

class Weight(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("The name of this weight, ie: Kilogram"))
    abbreviation = models.CharField(max_length=4, unique=True, verbose_name=_("Abbreviation"),
                                    help_text=_("An abbreviated name for this weight, used in reports, ie: Kg"))

    ratio_to_kilogram = models.DecimalField(max_digits=15, decimal_places=6, verbose_name=_("Ratio to Kilogram"))

    def format(self, value, use_comma, rounded=False, use_decimals=None, use_one_decimal_place=False):
        """
        Formats the passes in value, by converting from kilograms to this weight units
        """

        if value is None:
            return ""

        value = Decimal(value)

        is_negative = value < Decimal("0")
        value = abs( value / self.ratio_to_kilogram )

        if rounded:
            if use_one_decimal_place:
                value = value.quantize(Decimal('0.0'), ROUND_HALF_UP)
            else:
                value = value.quantize(Decimal('0.00'), ROUND_HALF_UP)

        if use_decimals is None:
            use_decimals = not rounded

        formatted = comma_formatted(value, use_decimals, use_comma, use_one_decimal_place)

        if is_negative:
            formatted = "-" + formatted

        return formatted

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)

class Currency(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("The name of this currency, ie: US Dollars"))
    currency_code = models.CharField(max_length=3, unique=True, verbose_name=_("Currency Code"),
                                     help_text=_("The international currency code for this currency, ie: USD, RWF"))
    abbreviation = models.CharField(max_length=4, unique=True, verbose_name=_("Abbreviation"),
                                    help_text=_("An abbreviated name for this currency, used in reports, ie: US$, RWF"))
    has_decimals = models.BooleanField(default=False, verbose_name=_("Has Decimals"),
                                       help_text=_("Whether this currency has decimals, ie: cents in US dollars"))
    prefix = models.CharField(default="", blank=True, max_length=4, verbose_name=_("Prefix"),
                              help_text=_("Any prefix to display before a value in this currency, ie: $"))
    suffix = models.CharField(default="", blank=True, max_length=4, verbose_name=_("Suffix"),
                              help_text=_("Any suffix to display after a value in this currency, ie: RWF"))

    def format(self, value, force_even=False, prefix_class=None, suffix_class=None):
        """
        Formats the passed in value according to this currency's rules.
        """
        if value is None:
            return ""

        has_decimals = self.has_decimals and not force_even
        if has_decimals:
            value = Decimal(value).quantize(Decimal(".01"), ROUND_HALF_UP)
        else:
            value = Decimal(value).quantize(Decimal("1"), ROUND_HALF_DOWN)

        is_negative = value < Decimal("0")
        value = abs(value)

        prefix = self.prefix
        if prefix_class and prefix:
            prefix = '<span class="%s">%s</span>' % (prefix_class, prefix)

        suffix = self.suffix
        if suffix_class and suffix:
            suffix = '<span class="%s">%s</span>' % (suffix_class, suffix)

        formatted = prefix + comma_formatted(value, has_decimals) + suffix

        if is_negative:
            formatted = "-" + formatted

        return mark_safe(formatted)

    def __unicode__(self):
        return self.name

    class Meta:
       verbose_name_plural = "Currencies"
       ordering = ('name',)       

class Country(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Country"),
                            help_text=_("The name of this country, ie: Rwanda"))
    country_code = models.CharField(max_length=2, unique=True, verbose_name=_("Country Code"),
                                    help_text=_("The two letter country code, ie: US, RW"))
    currency = models.ForeignKey(Currency, related_name="countries", verbose_name=_("Currency"),
                                 help_text=_("The local currency in this country."))
    weight = models.ForeignKey(Weight, related_name="countries", verbose_name=_("Weight"),
                               help_text=_("The common local weight unit used in this country"))

    language = models.CharField(max_length=10, choices=settings.LANGUAGES, verbose_name=_("Language"),
                                help_text=_("The language used in this country, reports will also be offered in this language"))
    calling_code = models.IntegerField(help_text=_("The country calling code for this country, leaving off the +, ie, 250 for Rwanda"),
                                       verbose_name=_("Calling Code"),
                                       validators = [MaxValueValidator(999)])
    phone_format = models.CharField(max_length=15, validators=[RegexValidator("[# -]+")], verbose_name=_("Phone Format"),
                                     help_text=_("The format to use when displaying phone numbers, use # signs for numbers as well as spaces and dashes, ie: ### ### ## ##"))
    national_id_format = models.CharField(max_length=35, validators=[RegexValidator("[# -]+")], verbose_name=_("National Id Format"),
                                          help_text=_("The format to use when displaying national ids, use # signs for numbers, A for letters, as well as spaces and dashes, ie: # #### # ####### # ##"))
    bounds_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, verbose_name=_("Bounds Latitude"))
    bounds_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, verbose_name=_("Bounds Longitude"))

    bounds_zoom = models.IntegerField(default=8, verbose_name="Bounds Zoom")

    def format_id(self, national_id):
        return format_string(self.national_id_format, national_id)        

    def format_phone(self, phone):
        return format_string(self.phone_format, phone)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ('name',)

def format_string(format, value):
    python_format = ''
    for idx in range(len(format)):
        char = format[idx]
        if char == '#' or char == 'A':
            python_format += "%s"
        else:
            python_format += char

    # we now have something that looks like like this: %s%s%s%s%s %s%s%s %s%s %s%s
    # we just need to build an argument list to go with it
    try:
        arguments = [value[i] for i in range(len(value))]
        return python_format % tuple(arguments)
    except:
        return value

class Province(SmartModel):
    name = models.CharField(max_length=64, verbose_name=_("Name"),
                            help_text=_("The name of this province, ie: Kigali"))
    country = models.ForeignKey(Country, verbose_name=_("Country"),
                                 help_text=_("The Country where this province belongs, ie: Rwanda"))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The number used to order the list of provinces, small comes first"))
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        ordering = ('country__name', 'order')
