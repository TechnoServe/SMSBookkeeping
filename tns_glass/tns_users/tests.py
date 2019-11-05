from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from guardian.shortcuts import remove_perm, assign

class UserTestCase(TNSTestCase):

    def test_permissions(self):
        # check permissions
        response = self.client.get(reverse('users.user_create'))
        self.assertRedirect(response, reverse('users.user_login'))

        # create a new user
        self.login(self.admin)
        response = self.client.get(reverse('users.user_create'))

        post_data = dict(username='james',
                         new_password='Rwanda123',
                         first_name='James',
                         last_name='Dargan',
                         email='james@rtc.com',
                         site_administrator='1',
                         country_administrator='1',
                         sms_administrator='1')

        # test creating a new user
        response = self.client.post(reverse('users.user_create'), post_data)
        james = User.objects.get(username='james')
        self.assertTrue(james.groups.filter(name="Administrators"))
        self.assertTrue(james.groups.filter(name="Country Administrators"))
        self.assertTrue(james.groups.filter(name="SMS Administrators"))

        # update, removing him as a site administrator
        update_url = reverse('users.user_update', args=[james.id])

        # take away his site admin
        post_data['is_active'] = True
        del post_data['site_administrator']
        del post_data['country_administrator']
        del post_data['sms_administrator']
        self.assertPost(update_url, post_data)

        # make sure his rights were taken away
        james = User.objects.get(username='james')
        self.assertFalse(james.groups.filter(name="Administrators"))
        self.assertFalse(james.groups.filter(name="Country Administrators"))
        self.assertFalse(james.groups.filter(name="SMS Administrators"))

        # then add them back
        post_data['site_administrator'] = 1
        post_data['country_administrator'] = 1
        post_data['sms_administrator'] = 1
        self.assertPost(update_url, post_data)

        james = User.objects.get(username='james')
        self.assertTrue(james.groups.filter(name="Administrators"))
        self.assertTrue(james.groups.filter(name="Country Administrators"))
        self.assertTrue(james.groups.filter(name="SMS Administrators"))

        permissions_url = reverse('users.user_permissions', args=[james.id])

        # we should be taken to the permissions page after creation
        self.assertRedirects(response, permissions_url)

        # ok, follow that redirection
        response = self.client.get(permissions_url)

        # we have five fields for each country, csp and wetmill.
        # our test config has two contries, three csps, and three wetmills
        # so total # of fields should be: (5*2 countries) + (5*3 csps) + (5*3 wetmills)
        
        # the above note is only true once we add all the permissions
        self.assertEquals(56, len(response.context['form'].fields))

        # give this user permissions to change wetmills in Rwanda and 
        # view SMS and edit SMS reports for RTC, and view and edit reports
        # at nasho
        post_data = dict(is_active=True)
        post_data['wetmill_edit__country_%d' % self.rwanda.id] = 1
        post_data['wetmill_edit__csp_%d' % self.rtc.id] = 1
        post_data['wetmill_edit__wetmill_%d' % self.nasho.id] = 1

        #TODO: when we get to these features we can add these tests in
#        post_data['sms_view__csp_%d' % self.rtc.id] = 1
#        post_data['sms_edit__csp_%d' % self.rtc.id] = 1
#        post_data['report_view__wetmill_%d' % self.nasho.id] = 1
#        post_data['report_edit__wetmill_%d' % self.nasho.id] = 1

        response = self.assertPost(permissions_url, post_data)

        # now test that those permissions were granted to james
        james = User.objects.get(username='james')
        self.assertTrue(james.has_perm('locales.country_wetmill_edit', self.rwanda))
        self.assertTrue(james.has_perm('csps.csp_wetmill_edit', self.rtc))
        self.assertTrue(james.has_perm('wetmills.wetmill_wetmill_edit', self.nasho))

        # get our permission page, make sure our initial data is right
        response = self.client.get(permissions_url)
        self.assertTrue('wetmill_edit__country_%d' % self.rwanda.id in response.context['form'].initial)

        # update them, removing rwanda
        del post_data['wetmill_edit__country_%d' % self.rwanda.id]
        response = self.assertPost(permissions_url, post_data)

        # validate that permission was removed
        james = User.objects.get(username='james')
        self.assertFalse(james.has_perm('locales.country_wetmill_edit', self.rwanda))
        self.assertTrue(james.has_perm('csps.csp_wetmill_edit', self.rtc))
        self.assertTrue(james.has_perm('wetmills.wetmill_wetmill_edit', self.nasho))                     
