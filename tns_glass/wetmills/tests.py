from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class WetmillTest(TNSTestCase):

    def test_unique_sms(self):
        self.login(self.admin)

        post_data = dict(country = self.rwanda.id,
                         name = "Musha",
                         sms_name = 'nasho',
                         description = "Musha is a better wetmill ever, ha?",
                         province = self.gitega.id,
                         year_started = 2009,
                         coordinates_lat = '-1.56824',
                         coordinates_lng = '29.35455')

        create_url = reverse('wetmills.wetmill_create')
        response = self.client.post(create_url, post_data)
        self.assertEquals(200, response.status_code)

    def test_crudl(self):
        self.login(self.admin)
        next_url = 'next='+reverse('wetmills.wetmill_create')
        pick_country_url = reverse('locales.country_pick') + '?' + next_url
        response = self.client.get(pick_country_url)
        self.assertIn(response.context['view'].get_context_data()['next'], next_url)

        post_data = dict(country=self.rwanda.id)
        response = self.client.post(pick_country_url, post_data, follow=True)
        self.assertEqual(response.context['form'].initial['country'], self.rwanda)

        create_url = reverse('wetmills.wetmill_create')
        self.assertEqual(create_url, response.request['PATH_INFO'])
        self.assertEqual(self.rwanda, response.context['form'].initial['country'])

        # make sure we only list rwanda provences, we shouldn't display any provences in kenya
        self.assertNotContains(response, "Kibirira")

        post_data = dict(country=self.rwanda.id,
                         name="Musha",
                         sms_name='musha',
                         description="Musha is a better wetmill ever, ha?",
                         province=self.gitega.id,
                         year_started=2009,
                         altitude=1050,
                         accounting_system='2012',
                         coordinates_lat='-1,56824',
                         coordinates_lng='29,35455')

        # should fail because cordinates use comma instead of period
        response = self.client.post(create_url, post_data)
        self.assertTrue('form' in response.context)
        self.assertTrue('coordinates' in response.context['form'].errors)

        post_data = dict(country=self.rwanda.id,
                         name="Musha",
                         sms_name='musha',
                         description="Musha is a better wetmill ever, ha?",
                         province=self.gitega.id,
                         year_started=2009,
                         altitude=1050,
                         accounting_system='2012',
                         coordinates_lat='-1.56824',
                         coordinates_lng='29.35455')

        response = self.client.post(create_url, post_data)
        self.assertEquals(302, response.status_code)

        wetmill = Wetmill.objects.get(name='Musha')
        self.assertEquals("Musha", str(wetmill))
        self.assertRedirect(response, reverse('wetmills.wetmill_list'))
        
        update_url = reverse('wetmills.wetmill_update', args=[wetmill.id])
        response = self.client.get(update_url)

        # assert our provences are only the ones in rwanda
        self.assertNotContains(response, "Kibirira")

        post_data['name'] = 'Musha2'
        post_data['coordinates_lat'] = ''
        post_data['coordinates_lng'] = ''

        # should fail because there are no coordinates
        response = self.client.post(update_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)

        post_data['coordinates_lat'] = '-1,5894'
        post_data['coordinates_lng'] = '29,3454'

        # should fail because coordinates use comma instead of period
        response = self.client.post(update_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)

        post_data['coordinates_lat'] = '-1.5894'
        post_data['coordinates_lng'] = '29.3454'

        response = self.assertPost(update_url,post_data)
        wetmill = Wetmill.objects.get(pk=wetmill.pk)
        self.assertEquals('Musha2', wetmill.name)

        response = self.client.get(reverse('wetmills.wetmill_list'))
        self.assertContains(response, 'Musha2')

    def test_crudl_permission(self):
        self.login(self.viewer)

        # by default, viewer's cannot update wetmills
        update_url = reverse('wetmills.wetmill_update', args=[self.nasho.id])
        response = self.client.get(update_url)
        self.assertRedirect(response, reverse('users.user_login'))

        # give the viewer permissions for nasho
        from guardian.shortcuts import get_objects_for_user, assign
        assign("%s_%s" % ('wetmill', 'wetmill_edit'), self.viewer, self.nasho)

        # try again
        response = self.client.get(update_url)
        self.assertEquals(200, response.status_code)

        # shouldn't work for the other wetmill
        response = self.client.get(reverse('wetmills.wetmill_update', args=[self.coko.id]))
        self.assertRedirect(response, reverse('users.user_login'))

        # shouldn't work for creating a wetmills
        response = self.client.get(reverse('wetmills.wetmill_create') + "?country=%d" % self.rwanda.id)
        self.assertRedirect(response, reverse('users.user_login'))

        # unless we give them country level
        assign("%s_%s" % ('country', 'wetmill_edit'), self.viewer, self.rwanda)

        response = self.client.get(reverse('wetmills.wetmill_update', args=[self.coko.id]))
        self.assertEquals(200, response.status_code)

        # make sure a post works
        post_data = dict(country = self.rwanda.id,
                         name = "Musha",
                         sms_name = 'musha',
                         description = "Musha is a better wetmill ever, ha?",
                         province = self.gitega.id,
                         year_started = 2009,
                         altitude=1050,
                         accounting_system='2012',
                         coordinates_lat = '-1.56824',
                         coordinates_lng = '29.35455')

        response = self.client.post(reverse('wetmills.wetmill_update', args=[self.coko.id]), post_data)
        self.assertRedirect(response, reverse('public-wetmill', args=[self.coko.id]))

        # make sure we can also create a new wetmill
        response = self.client.get(reverse('wetmills.wetmill_create') + "?country=%d" % self.rwanda.id)
        self.assertEquals(200, response.status_code)

        post_data['name'] = "Test"
        post_data['sms_name'] = "Test"
        response = self.client.post(reverse('wetmills.wetmill_create') + "?country=%d" % self.rwanda.id, post_data)
        self.assertRedirect(response, reverse('public-country', args=[self.rwanda.country_code]))

        # no dice for kenya though
        response = self.client.get(reverse('wetmills.wetmill_update', args=[self.kaguru.id]))
        self.assertRedirect(response, reverse('users.user_login'))

    def test_ordering(self):
        self.login(self.admin)
        
        # clear out existing wetmills, we want to test the order of just the ones
        # we create below
        Wetmill.objects.all().delete()

        rwanda_zaon = Wetmill.objects.create(country=self.rwanda,name='Zaon',sms_name='zaon',description='zaon',province=self.gitega,
                                             year_started=2005, created_by=self.admin, modified_by=self.admin)
        kenya_habari = Wetmill.objects.create(country=self.kenya,name='Habari',sms_name='habari',description='habari',province=self.kibirira,
                                                   year_started=2005,created_by=self.admin, modified_by=self.admin)
        rwanda_biryogo = Wetmill.objects.create(country=self.rwanda,name='Biryogo',sms_name='biryogo',description='biryogo',province=self.bwanacyambwe,
                                                   year_started=2005,created_by=self.admin, modified_by=self.admin)
        kenya_sanaga = Wetmill.objects.create(country=self.kenya,name='Sanaga',sms_name='sanaga',description='sanaga',province=self.mucoma,
                                                   year_started=2005, created_by=self.admin, modified_by=self.admin)
        rwanda_abatarutwa = Wetmill.objects.create(country=self.rwanda,name='Abatarutwa',sms_name='abatarutwa',description='abatarutwa',province=self.gitega,
                                                   year_started=2005, created_by=self.admin, modified_by=self.admin)
        kenya_kelicho = Wetmill.objects.create(country=self.kenya,name='Kelicho',sms_name='kelicho',description='kelicho',province=self.mucoma,
                                                   year_started=2005, created_by=self.admin, modified_by=self.admin)

        response = self.client.get(reverse('wetmills.wetmill_list'))
        wetmills = response.context['wetmill_list']
        self.assertEquals(kenya_habari, wetmills[0])
        self.assertEquals(kenya_kelicho, wetmills[1])
        self.assertEquals(kenya_sanaga, wetmills[2])
        self.assertEquals(rwanda_abatarutwa, wetmills[3])
        self.assertEquals(rwanda_biryogo, wetmills[4])
        self.assertEquals(rwanda_zaon, wetmills[5])

    def test_update_csps(self):
        self.login(self.admin)
        csp_url = reverse('wetmills.wetmill_csps', args=[self.nasho.id])

        # shouldn't have a current csp
        self.assertEquals(None, self.nasho.current_csp())

        response = self.client.get(csp_url)
        self.assertEquals(2, len(response.context['form'].fields))
        self.assertContains(response, "Rwanda 2009")
        self.assertContains(response, "Rwanda 2010")

        # associate csp's for both our rwandan seasons
        post_data = dict()
        post_data['csp__%d' % self.rwanda_2009.id] = self.rtc.id
        post_data['csp__%d' % self.rwanda_2010.id] = self.rwacof.id
        response = self.assertPost(csp_url, post_data)

        # rwacof should be current
        self.assertEquals(self.rwacof, self.nasho.current_csp())

        # assert our db is in sync
        self.assertEquals(self.rtc, self.nasho.get_csp_for_season(self.rwanda_2009))
        self.assertEquals(self.rwacof, self.nasho.get_csp_for_season(self.rwanda_2010))
        self.assertEquals(None, self.nasho.get_csp_for_season(self.kenya_2011))

        # test the initial data when viewing the form again
        response = self.client.get(csp_url)
        self.assertEquals(self.rtc.id, response.context['form'].initial['csp__%d' % self.rwanda_2009.id])

        # now update again, clearing out our 2010 mapping
        del post_data['csp__%d' % self.rwanda_2010.id]
        response = self.assertPost(csp_url, post_data)
        
        # check the db once more
        self.assertEquals(self.rtc, self.nasho.get_csp_for_season(self.rwanda_2009))
        self.assertEquals(None, self.nasho.get_csp_for_season(self.rwanda_2010))
        self.assertEquals(None, self.nasho.get_csp_for_season(self.kenya_2011))

        # we shouldn't have a current csp anymore either
        self.assertEquals(None, self.nasho.current_csp())

        # test our get method as well
        season_csps = self.nasho.get_season_csps()
        self.assertEquals(1, len(season_csps))
        self.assertEquals(self.rtc, season_csps[0].csp)
        self.assertEquals(self.rwanda_2009, season_csps[0].season)
        self.assertEquals("Rwanda 2009 - Rwanda Trading Company = Nasho", str(season_csps[0]))

    def test_import_views(self):
        response = self.client.get(reverse('wetmills.wetmillimport_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        response = self.client.get(reverse('wetmills.wetmillimport_list'))
        self.assertEquals(200, response.status_code)

        create_url = reverse('wetmills.wetmillimport_create')
        response = self.client.get(create_url)
        f = open(self.build_import_path("wetmill_import.csv"))
        post_data = dict(csv_file=f, country=self.rwanda.id)

        response = self.assertPost(create_url, post_data)
        wm_import = WetmillImport.objects.get()
        self.assertEquals('PENDING', wm_import.get_status())

        wm_import.import_log = ""
        wm_import.save()

        wm_import.log("hello world")
        wm_import = WetmillImport.objects.get()        
        self.assertEquals("hello world\n", wm_import.import_log)

        response = self.client.get(reverse('wetmills.wetmillimport_read', args=[wm_import.id]))
        self.assertContains(response, "PENDING")

        response = self.client.get(reverse('wetmills.wetmillimport_list'))
        self.assertContains(response, "PENDING")

    def build_import_path(self, name):
        import os
        from django.conf import settings
        return os.path.join(settings.TESTFILES_DIR, name)

    def test_import(self):
        east = Province.objects.create(name="East", country=self.rwanda, order=2, created_by=self.admin, modified_by=self.admin)
        west = Province.objects.create(name="West", country=self.rwanda, order=3, created_by=self.admin, modified_by=self.admin)

        path = self.build_import_path("wetmill_import.csv")

        # clear existing wetmills
        Wetmill.objects.all().delete()
        wetmills = import_csv_wetmills(self.rwanda, path, self.admin)
        
        self.assertEquals(2, len(wetmills))

        nasho = Wetmill.objects.get(name="Nasho")
        self.assertEquals("Nasho", nasho.name)
        self.assertEquals("East", nasho.province.name)
        self.assertEquals("nasho", nasho.sms_name)
        self.assertEquals(2010, nasho.year_started)
        self.assertDecimalEquals("-1.99", nasho.latitude)
        self.assertDecimalEquals("30.02", nasho.longitude)
        self.assertEquals(1539, nasho.altitude)

        git = Wetmill.objects.get(name="Gitarama")
        self.assertEquals("Gitarama", git.name)
        self.assertEquals("West", git.province.name)
        self.assertEquals("gitarama", git.sms_name)
        self.assertIsNone(git.year_started)
        self.assertIsNone(git.latitude)
        self.assertIsNone(git.longitude)
        self.assertIsNone(git.altitude)

        # change one of nasho's values
        nasho.sms_name = "somethingdiff"
        nasho.save()

        # import again, should be brought back
        wetmills = import_csv_wetmills(self.rwanda, path, self.admin)

        nasho = Wetmill.objects.get(name="Nasho")
        self.assertEquals("nasho", nasho.sms_name)

    def assertBadImport(self, filename, error):
        path = self.build_import_path(filename)

        try:
            reports = import_csv_wetmills(self.rwanda, path, self.admin)
            self.fail("Should have thrown error.")
        except Exception as e:
            self.assertIn(error, str(e))

    def test_bad_imports(self):
        east = Province.objects.create(name="East", country=self.rwanda, order=2, created_by=self.admin, modified_by=self.admin)
        west = Province.objects.create(name="West", country=self.rwanda, order=3, created_by=self.admin, modified_by=self.admin)

        self.assertBadImport("wetmill_import_no_name.csv", "Missing name for row")
        self.assertBadImport("wetmill_import_no_province.csv", "Missing province for row")
        self.assertBadImport("wetmill_import_bad_province.csv", "Unable to find province")
        self.assertBadImport("wetmill_import_no_sms.csv", "Missing sms name for")
        self.assertBadImport("wetmill_import_bad_header.csv", "CSV file missing the header")
        self.assertBadImport("wetmill_import_bad_decimal.csv", "Invalid decimal value")




        
        
        
