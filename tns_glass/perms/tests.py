from django.test import TestCase
from tns_glass.tests import TNSTestCase
from perms.templatetags.perms import set_has_wetmill_permission
from perms.models import has_wetmill_permission
from guardian.shortcuts import remove_perm, assign
from seasons.models import Season

class PermTestCase(TNSTestCase):

    def test_not_logged_in(self):
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))

    def test_has_country(self):
        assign('locales.country_wetmill_edit', self.viewer, self.rwanda)
        self.assertTrue(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))
        self.assertTrue(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))

        self.assertFalse(has_wetmill_permission(self.viewer, self.kaguru, 'wetmill_edit'))
        
        # the admin user have global access thus he has permission to any wetmill
        self.assertTrue(has_wetmill_permission(self.admin, self.kaguru, 'wetmill_edit'))

    def test_has_wetmill(self):
        # grant permissions to on the wetmill to the viewer user
        assign('wetmills.wetmill_wetmill_edit', self.viewer, self.nasho)
        self.assertTrue(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))
        self.assertTrue(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))

        # the admin has global access to this wetmill too
        self.assertTrue(has_wetmill_permission(self.admin, self.nasho, 'wetmill_edit', self.rwanda_2009))        

    def test_has_csp(self):
        assign('csps.csp_wetmill_edit', self.viewer, self.rtc)

        # nasho isn't associated with any CSPs for any season, so no access
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))
        
        # but as the admin has the full access to any csp there visit to nasho wont be a problem
        self.assertTrue(has_wetmill_permission(self.admin, self.nasho, 'wetmill_edit'))
        self.assertTrue(has_wetmill_permission(self.admin, self.nasho, 'wetmill_edit', self.rwanda_2009))

        # let's add RTC as the CSP for rwanda for 2010
        self.nasho.set_csp_for_season(self.rwanda_2010, self.rtc)

        # true, the most recent season of 2010 is implied
        self.assertTrue(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))

        # false, RTC isn't the CSP for 2009
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))

        # remove all seasons, try again
        Season.objects.all().delete()
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit'))
        self.assertFalse(has_wetmill_permission(self.viewer, self.nasho, 'wetmill_edit', self.rwanda_2009))

    def test_template_tag(self):
        context = dict(user=self.viewer)
        output = set_has_wetmill_permission(context, self.nasho, 'wetmill_edit')
        self.assertEquals(0, len(str(output)))
        self.assertFalse(context['wetmill_edit'])
    
        
