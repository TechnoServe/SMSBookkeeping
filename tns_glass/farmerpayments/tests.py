from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class FarmerPaymentTestCase(TNSTestCase):

    def test_crudl(self):
        # make sure we can't view these without being logged in
        list_url = reverse('farmerpayments.farmerpayment_list')
        response = self.client.get(list_url)
        self.assertRedirect(response, reverse('users.user_login'))

        # create a new cash use
        self.login(self.admin)

        FarmerPayment.objects.all().delete()

        create_url = reverse('farmerpayments.farmerpayment_create')

        response = self.client.get(create_url)
        self.assertNotContains(response, "is_active")
        self.assertContains(response, "name")

        post_data = dict(name="Second Payment", order=0)
        response = self.assertPost(create_url, post_data)

        fp = FarmerPayment.objects.get()
        self.assertEquals("Second Payment", str(fp))
        self.assertEquals("Second Payment", fp.name)

        update_url = reverse('farmerpayments.farmerpayment_update', args=[fp.id])

        response = self.client.get(update_url)
        self.assertContains(response, "is_active")
        self.assertEquals("Second Payment", response.context['form'].initial['name'])

        post_data = dict(name="Farmer Payment", order=0, is_active=1)
        response = self.assertPost(update_url, post_data)

        fp = FarmerPayment.objects.get()
        self.assertEquals("Farmer Payment", fp.name)
        self.assertEquals("Farmer Payment", str(fp.name))
        response = self.client.get(list_url)

        self.assertContains(response, "Farmer Payment")

