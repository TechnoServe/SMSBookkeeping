from django import template
from ..models import has_wetmill_permission, has_csp_permission, has_country_permission, has_any_permission

register = template.Library()

@register.simple_tag(takes_context=True)
def set_has_wetmill_permission(context, wetmill, permission, season=None):
    """
    Should return whether there is a user logged in, and if so, whether they have
    the passed in permission on this wetmill (and optionally season)

    {% has_perm wetmill 'change_wetmill' season %}
    """
    # not logged in, then no access
    if not 'user' in context:
        context[permission] = False
        return ''

    user = context['user']
    context[permission] = has_wetmill_permission(user, wetmill, permission, season)

    # we don't want to output anytime to the template
    return ''

@register.simple_tag(takes_context=True)
def set_has_any_permission(context, permission):
    # not logged in, then no access
    if not 'user' in context:
        context[permission] = False
        return ''

    user = context['user']
    context[permission] = has_any_permission(user, permission)

    # we don't want to output anytime to the template
    return ''

@register.simple_tag(takes_context=True)
def set_has_country_permission(context, country, permission):
    if not 'user' in context:
        context[permission] = False
        return ''

    user = context['user']

    # see if they have access at the country level
    context[permission] = has_country_permission(user, country, permission)

    # don't output anything to the template
    return ''

@register.simple_tag(takes_context=True)
def set_has_csp_permission(context, csp, permission):
    if not 'user' in context:
        context[permission] = False
        return ''

    user = context['user']

    # see if they have access at the csp level
    context[permission] = has_csp_permission(user, csp, permission)

    # don't output anything to the template
    return ''

