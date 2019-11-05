from django.contrib.auth.models import Permission
from guardian.models import UserObjectPermission
from guardian.shortcuts import get_objects_for_user
from locales.models import Country
from seasons.models import Season
from wetmills.models import Wetmill, WetmillCSPSeason


def has_csp_permission(user, csp, permission):
    """
    Returns whether the passed in user has the passed in permission on this CSP
    """
    if user.has_perm('csps.csp_%s' % permission):
        return True

    if user.has_perm('csps.csp_%s' % permission, csp):
        return True

    if user.has_perm('locales.country_%s' % permission):
        return True

    # see if they have access at the country level
    if user.has_perm('locales.country_%s' % permission, csp.country):
        return True

    return False

def has_country_permission(user, country, permission):
    """
    Returns whether the passed in user has the passed in permission on this country
    """
    if user.has_perm('locales.country_%s' % permission):
        return True

    if user.has_perm('locales.country_%s' % permission, country):
        return True

    return False

def get_all_wetmills_with_permission(user, permission):
    """
    Returns a query set of all the wetmills that the user has the permission
    for, checking country, csp and wetmill in the process
    """
    # no wetmills if you aren't logged in
    if user.is_anonymous():
        return Wetmill.objects.filter(pk__lte=-1)

    wetmill_ids = set()
    for country in get_objects_for_user(user, 'locales.country_' + permission):
        for wetmill in Wetmill.objects.filter(country=country):
            wetmill_ids.add(wetmill.pk)

    # get all the csp permissions
    for csp in get_objects_for_user(user, 'csps.csp_' + permission):
        for wetmill in WetmillCSPSeason.objects.filter(csp=csp):
            wetmill_ids.add(wetmill.wetmill_id)

    # get all wetmill permissions
    for wetmill in get_objects_for_user(user, 'wetmills.wetmill_' + permission):
        wetmill_ids.append(wetmill.id)

    return Wetmill.objects.filter(pk__in=wetmill_ids)

def get_wetmills_with_permission(user, season, permission):
    """
    Returns a query set of all the wetmills that the user has the permission
    for, checking country, csp and wetmill in the process
    """
    # no wetmills if you aren't logged in
    if user.is_anonymous():
        return Wetmill.objects.filter(pk__lte=-1)

    # SMS admin gets to see every wetmill in this season
    if user.has_perm('dashboard.assumptions_dashboard'):
        return Wetmill.objects.filter(country=season.country)

    if user.has_perm('country_' + permission, season.country):
        return Wetmill.objects.filter(country=season.country)

    # get all the csp permissions
    wetmill_ids = []
    for csp in get_objects_for_user(user, 'csps.csp_' + permission):
        if csp.country_id == season.country_id:
            for wetmill in WetmillCSPSeason.objects.filter(season=season, csp=csp):
                wetmill_ids.append(wetmill.wetmill_id)

    # get all wetmill permissions
    for wetmill in get_objects_for_user(user, 'wetmills.wetmill_' + permission):
        if wetmill.country_id == season.country_id:
            wetmill_ids.append(wetmill.id)

    return Wetmill.objects.filter(pk__in=wetmill_ids)

def has_any_permission(user, permission):
    """
    Checks whether the passed in user has the passed in permission on any object at all
    """
    if user.is_anonymous():
        return False

    for object_type in ('wetmill', 'csp', 'country'):
        type_permission = '%s_%s' % (object_type, permission)

        has_perm = user.has_perm(type_permission)
        if has_perm: return True

        permission_id = Permission.objects.get(codename=type_permission).id

        # return whether we have this permission on any object
        has_perm = UserObjectPermission.objects.filter(user=user, permission=permission_id)
        if has_perm: return True

    return False

def has_wetmill_permission(user, wetmill, permission, season=None):
    """
    Should return whether there is a user logged in, and if so, whether they have
    the passed in permission on this wetmill (and optionally season)
    """
    # see if they have access on this particular wetmill
    if user.has_perm('wetmills.wetmill_%s' % permission) or user.has_perm('wetmills.wetmill_%s' % permission, wetmill):
        return True

    if not wetmill:
        return False

    # see if they have access at the country level
    if user.has_perm('locales.country_%s' % permission, wetmill.country) or user.has_perm('locales.country_%s' % permission):
        return True

    # at this point, we need to check the CSP permission, figure out what CSP is associated
    # with this wetmill for the passed in season

    # no season passed in implies latest
    if not season:
        seasons = Season.objects.filter(country=wetmill.country, is_active=True)
        if seasons:
            season = seasons[0]

    csp = wetmill.get_csp_for_season(season)

    # if we have a csp, check whether the user has permission on that csp
    if csp:
        return user.has_perm('csps.csp_%s' % permission, csp) or user.has_perm('csps.csp_%s' % permission)

    # otherwise, no permission
    else:
        return False
