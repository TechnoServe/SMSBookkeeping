from django import template
from django.template import TemplateSyntaxError
from locales.templatetags.locales import *
import re

register = template.Library()

def cell(context, values, key, tooltip_block, formatter, placement):
    if formatter == format_currency or formatter == format_currency_rounded:
        currency = context.get('currency')
        value = formatter(values.get(key, None), currency)
    elif formatter == format_weight:
        dashboard_weight = context.get('dashboard_weight')
        value = formatter(values.get(key, None), dashboard_weight)
        if value:
            value = value + " " + dashboard_weight.abbreviation

    else:
        value = formatter(values.get(key, None))

    tooltip = None
    if tooltip_block:
        blocks = context.get('blocks', None)
        if blocks:
            tooltip = blocks.get(tooltip_block, None)

    if tooltip and value != '-':
        tooltip = re.sub(" +", " ", tooltip.strip())
        return "<a href='#' onClick='return false;' class='more' data-toggle='tooltip' data-placement='%s' title='%s'>%s</a>" % (placement, tooltip, value)
    else:
        return value

@register.simple_tag(takes_context=True)
def weight_cell(context, values, key, tooltip_block=None, placement='top'):
    return cell(context, values, key, tooltip_block, format_weight, placement)

@register.simple_tag(takes_context=True)
def percent_cell(context, values, key, tooltip_block=None, placement='top'):
    return cell(context, values, key, tooltip_block, format_percent, placement)

@register.simple_tag(takes_context=True)
def tons_cell(context, values, key, tooltip_block=None, placement='top'):
    return cell(context, values, key, tooltip_block, format_tons, placement)

@register.simple_tag(takes_context=True)
def currency_cell(context, values, key, tooltip_block=None, placement='top'):
    return cell(context, values, key, tooltip_block, format_currency, placement)

@register.simple_tag(takes_context=True)
def currency_cell_rounded(context, values, key, tooltip_block=None, placement='top'):
    return cell(context, values, key, tooltip_block, format_currency_rounded, placement)

@register.simple_tag(takes_context=True)
def warn_for_variance(context, values, key):
    if not key in values:
        return ""
    else:
        value = values[key]
        if value < Decimal("-15") or value > Decimal("15"):
            return "warn "
        else:
            return ""

@register.simple_tag(takes_context=True)
def warn_for_percentage(context, values, key):
    if not key in values:
        return ""
    else:
        value = values[key]
        if value < Decimal("85") or value > Decimal("115"):
            return "warn "
        else:
            return ""

@register.filter(name='as_form_date')
def as_form_date(value):
    if not value:
        return ''
    else:
        return value.strftime("%B %d, %Y")

@register.inclusion_tag('dashboard/assumption_field.html', takes_context=True)
def render_assumption_field(context, field):
    form = context['form']
    view = context['view']

    readonly_fields = view.derive_readonly()

    # check that this field exists in our form, either as a real field or as a readonly one
    if not field in form.fields and not field in readonly_fields:
        raise TemplateSyntaxError("Error: No field '%s' found in form to render" % field)

    inclusion_context = dict(field=field,
                             form=context['form'],
                             view=context['view'],
                             blocks=context['blocks'],
                             defaults=context['defaults'])
    if 'object' in context:
        inclusion_context['object'] = context['object']

    return inclusion_context

@register.filter
def convert_currency(value, exchange_rate):
    if convert_currency:
        return value / Decimal(exchange_rate)
    return value
