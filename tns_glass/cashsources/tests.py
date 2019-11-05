from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class CashSourceTestCase(TNSTestCase):

    def test_crudl(self):
        # make sure we can't view these without being logged in
        list_url = reverse('cashsources.cashsource_list')
        response = self.client.get(list_url)
        self.assertRedirect(response, reverse('users.user_login'))

        # create a new cash use
        self.login(self.admin)

        CashSource.objects.all().delete()

        create_url = reverse('cashsources.cashsource_create')

        response = self.client.get(create_url)
        self.assertNotContains(response, "is_active")
        self.assertContains(response, "name")

        post_data = dict(name="Cash Due from CSP", order=0, calculated_from='NONE')
        response = self.assertPost(create_url, post_data)

        cs = CashSource.objects.get()
        self.assertEquals("Cash Due from CSP", str(cs))
        self.assertEquals("Cash Due from CSP", cs.name)

        update_url = reverse('cashsources.cashsource_update', args=[cs.id])

        response = self.client.get(update_url)
        self.assertContains(response, "is_active")
        self.assertEquals("Cash Due from CSP", response.context['form'].initial['name'])

        post_data = dict(name="Cash Due", order=0, is_active=1, calculated_from='CDUE')
        response = self.assertPost(update_url, post_data)

        cs = CashSource.objects.get()
        self.assertEquals("Cash Due", cs.name)
        self.assertEquals("Cash Due", str(cs.name))
        self.assertEquals('CDUE', cs.calculated_from)
        response = self.client.get(list_url)

        self.assertContains(response, "Cash Due")

        
