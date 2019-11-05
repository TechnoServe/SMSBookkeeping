from django import template
from datetime import datetime
from django.utils import simplejson
from ..models import comma_formatted
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
import pytz
from decimal import Decimal

register = template.Library()

@register.filter
def local_timezone(value, format="%b %e %Y, %H:%M"):
    local = pytz.timezone(settings.USER_TIME_ZONE)
    value = value.replace(tzinfo=pytz.utc)
    return value.astimezone(local).strftime(format)

@register.filter
def format_int(value):
    try:
        value = int(value)
        return intcomma(value)
    except:
        return intcomma(value)

@register.filter
def format_percent(value):
    if value is None:
        return "-"

    try:
        value = int(value)
        return intcomma(value) + "%"
    except:
        return intcomma(value) + "%"

@register.filter
def format_currency(price, currency):
    if price is None or price == '':
        return "-"
    else:
        try:
            return currency.format(price)
        except:
            return price

@register.filter
def format_currency_summary(price, currency):
    if price is None or price == '':
        return "-"
    else:
        try:
            return currency.format(price, False, "med", "med")
        except:
            return price

@register.filter
def format_currency_rounded(price, currency):
    if price is None or price == '':
        return "-"
    else:
        try:
            return currency.format(price, True)
        except:
            return price

@register.filter
def format_currency_rounded_summary(price, currency):
    if price is None or price == '':
        return "-"
    else:
        try:
            return currency.format(price, True, "med", "med")
        except:
            return price

@register.filter
def format_kilos(value):
    if value is None or value == '':
        return "-"
    else:
        return comma_formatted(value, False) + " Kg"

@register.filter
def format_tons(value):
    if value is None or value == '':
        return "-"
    else:
        tons = comma_formatted((value / Decimal(1000)).quantize(Decimal(".01")), True)
        return str(tons) + " mT"

@register.filter
def format_id(national_id, country):
    return country.format_id(national_id)

@register.filter
def format_phone(phone, country):
    return country.format_phone(phone)

@register.filter
def format_weight(value, weight):
    if value is None or value == '':
        return ""
    else:
        try:
            return weight.format(value, True)
        except:
            return value

@register.filter
def format_weight_int(value, weight):
    if value is None or value == '':
        return ''
    else:
        try:
            return weight.format(value, False)
        except:
            return value

@register.filter
def format_weight_rounded(value, weight):
    if value is None or value == '':
        return ''
    else:
        try:
            return weight.format(value, True, True)
        except:
            return value


@register.filter
def format_weight_rounded_use_decimals(value, weight):
    if value is None or value == '':
        return ''
    else:
        try:
            return weight.format(value, True, True, True)
        except:
            return value

@register.filter
def format_weight_rounded_use_one_decimal_place(value, weight):
    if value is None or value == '':
        return ''
    else:
        try:
            return weight.format(value, True, True, True, True)
        except:
            return value