from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import CashUse

class CashUseTestCase(TNSTestCase):

    def test_crudl(self):
        # make sure we can't view these without being logged in
        list_url = reverse('cashuses.cashuse_list')
        response = self.client.get(list_url)
        self.assertRedirect(response, reverse('users.user_login'))

        # create a new cash use
        self.login(self.admin)

        CashUse.objects.all().delete()

        create_url = reverse('cashuses.cashuse_create')

        response = self.client.get(create_url)
        self.assertNotContains(response, "is_active")
        self.assertContains(response, "name")

        post_data = dict(name="Dividend", order=0, calculated_from='NONE')
        response = self.assertPost(create_url, post_data)

        cu = CashUse.objects.get()
        self.assertEquals("Dividend", str(cu))
        self.assertEquals("Dividend", cu.name)

        update_url = reverse('cashuses.cashuse_update', args=[cu.id])

        response = self.client.get(update_url)
        self.assertContains(response, "is_active")
        self.assertEquals("Dividend", response.context['form'].initial['name'])

        post_data = dict(name="Member Dividend", order=0, is_active=1, calculated_from='NONE')
        response = self.assertPost(update_url, post_data)

        cu = CashUse.objects.get()
        self.assertEquals("Member Dividend", cu.name)
        response = self.client.get(list_url)

        self.assertContains(response, "Member Dividend")

        
