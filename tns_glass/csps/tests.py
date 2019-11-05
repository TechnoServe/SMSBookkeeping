from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class CSPTest(TNSTestCase):
    def test_crudl(self):
        self.login(self.admin)

        post_data = dict(name="RCA",
                         sms_name="rca",
                         country = self.rwanda.id,
                         description = "Rwanda Coffee Association",
                         order='1')

        response = self.assertPost(reverse('csps.csp_create'), post_data)
        csp = CSP.objects.get(name='RCA')

        update_url = reverse('csps.csp_update', args=[csp.id])
        response = self.client.get(update_url)
        post_data['name'] = "Kigali Kawa"

        response = self.assertPost(update_url, post_data)
        csp = CSP.objects.get(name="Kigali Kawa")

        response = self.client.get(reverse('csps.csp_list'))
        self.assertContains(response, "Kigali Kawa")

        self.assertEquals(csp.name, '%s' % csp)

    def test_ordering(self):
        csps = CSP.objects.all()

        self.assertEquals(self.wetu, csps[0])
        self.assertEquals(self.rwacof, csps[1])
        self.assertEquals(self.rtc, csps[2])

