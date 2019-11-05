from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from scorecards.models import *
from standards.models import *

from guardian.shortcuts import remove_perm, assign

class ScorecardTestCase(TNSTestCase):
    def test_crudl(self):
        # not logged in, go to login
        response = self.client.get(reverse('scorecards.scorecard_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        scorecard = Scorecard.objects.create(season=self.rwanda_2010, wetmill=self.nasho,
                                             created_by=self.admin, modified_by=self.admin)
        self.login(self.admin)
        post_data = dict(season=self.rwanda_2010.id,
                         wetmill=self.nasho.id,
                         client_id='N/A',
                         auditor='KEZA Ane',
                         audit_date="October 20, 2011")
        self.assertPost(reverse('scorecards.scorecard_update', args=[scorecard.id]), post_data)
        scorecard = Scorecard.objects.get(pk=scorecard.pk)
        self.assertEquals("KEZA Ane", scorecard.auditor)

        scorecard_nasho_2009 = Scorecard.objects.create(season=self.rwanda_2009, wetmill=self.nasho,
                                                        created_by=self.admin, modified_by=self.admin)
        scorecard_coko_2009 = Scorecard.objects.create(season=self.rwanda_2009, wetmill=self.coko,
                                                       created_by=self.admin, modified_by=self.admin)
        scorecard_coko_2010 = Scorecard.objects.create(season=self.rwanda_2010, wetmill=self.coko,
                                                       created_by=self.admin, modified_by=self.admin)
        scorecard_kaguru_2011 = Scorecard.objects.create(season=self.kenya_2011, wetmill=self.kaguru,
                                                         created_by=self.admin, modified_by=self.admin)

        response = self.client.get(reverse('scorecards.scorecard_list'))
        scorecards = response.context['scorecard_list']

        self.assertEquals(scorecard_kaguru_2011, scorecards[0])
        self.assertEquals(scorecard_coko_2009, scorecards[1])
        self.assertEquals(scorecard_nasho_2009, scorecards[2])
        self.assertEquals(scorecard_coko_2010, scorecards[3])
        self.assertEquals(scorecard, scorecards[4])

        # test the object name itself
        self.assertEquals("2009 Nasho Scorecard", str(scorecard_nasho_2009.__unicode__()))

        Scorecard.objects.all().delete()

    def setUpStandards(self):
        StandardCategory.objects.all().delete()
        Standard.objects.all().delete()

        # adding standard categories
        self.SRE = StandardCategory.objects.create(name='Social Responsibility & Ethics', acronym='SRE', order=1,
                                                   created_by=self.admin, modified_by=self.admin)
        self.OHS = StandardCategory.objects.create(name='Occupational Health & Safety', acronym='OHS', order=2,
                                                   created_by=self.admin, modified_by=self.admin)
        self.ER = StandardCategory.objects.create(name='Environmental Responsibility', acronym='ER', order=3,
                                                  created_by=self.admin, modified_by=self.admin)

        self.SRE1 = Standard.objects.create(name='No Child Labour', category=self.SRE, kind='MR', order=1,
                                            created_by=self.admin, modified_by=self.admin)
        self.SRE2 = Standard.objects.create(name='No Forced Labour', category=self.SRE, kind='MR', order=2,
                                            created_by=self.admin, modified_by=self.admin)
        self.SRE3 = Standard.objects.create(name='No Discrimination', category=self.SRE, kind='MR', order=3,
                                            created_by=self.admin, modified_by=self.admin)
        self.SRE4 = Standard.objects.create(name='Minimum Wage', category=self.SRE, kind='MR', order=4,
                                            created_by=self.admin, modified_by=self.admin)

        self.OHS1 = Standard.objects.create(name='Occupational Health and Safety Policy', category=self.OHS, kind='BP',
                                            order=1, created_by=self.admin, modified_by=self.admin)
        self.OHS2 = Standard.objects.create(name='Annual Health and Safety Risk Assessment', category=self.OHS,
                                            kind='BP', order=2,
                                            created_by=self.admin, modified_by=self.admin)
        self.OHS3 = Standard.objects.create(name='Occupational Health and Safety Training', category=self.OHS,
                                            kind='BP', order=3, created_by=self.admin, modified_by=self.admin)
        self.OHS4 = Standard.objects.create(name='Medical Emergency Plan and First Aid Training', category=self.OHS,
                                            kind='BP', order=4, created_by=self.admin, modified_by=self.admin)

        self.ER1 = Standard.objects.create(name='Waste Water Management', category=self.ER, kind='MR', order=1,
                                           created_by=self.admin, modified_by=self.admin)
        self.ER2 = Standard.objects.create(name='Environmental Practices Policy', category=self.ER, kind='MR', order=2,
                                           created_by=self.admin, modified_by=self.admin)
        self.ER3 = Standard.objects.create(name='Waste Management - Coffee Pulp', category=self.ER, kind='BP', order=3,
                                           created_by=self.admin, modified_by=self.admin)
        self.ER4 = Standard.objects.create(name='Tracking Water Consumption', category=self.ER, kind='BP', order=4,
                                           created_by=self.admin, modified_by=self.admin)

    def test_scorecard_editing(self):
        # not logged in, go to login page
        response = self.client.get(reverse('scorecards.scorecard_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, reverse('users.user_login'))

        # shouldn't be a scorecard for nasho, 2010 yet
        self.assertEquals(0, Scorecard.objects.filter(wetmill=self.nasho, season=self.rwanda_2010).count())

        # assign view permission the the viewer user
        assign("wetmills.wetmill_scorecard_view", self.viewer)
        self.login(self.viewer)

        # first time doing a lookup, we'll actually create the Scorecard
        response = self.client.get(reverse('scorecards.scorecard_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, reverse('users.user_login'))        
        self.client.logout()        

        # finalize the scorecard
        scorecard = Scorecard.objects.create(wetmill=self.nasho, season=self.rwanda_2010, created_by=self.admin, modified_by=self.admin)
        scorecard = Scorecard.objects.get(wetmill=self.nasho, season=self.rwanda_2010)
        read_url = reverse('scorecards.scorecard_read', args=[scorecard.id])
        scorecard.is_finalized = True
        scorecard.save()

        # second time through it already exists, so should return the same scorecard
        self.login(self.viewer)
        response = self.client.get(reverse('scorecards.scorecard_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, read_url)
        # delete the report object after use
        #scorecard.delete()
        self.client.logout()

        self.login(self.admin)
        response = self.client.get(reverse('scorecards.scorecard_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertEquals(1, Scorecard.objects.filter(wetmill=self.nasho, season=self.rwanda_2010).count())
        scorecard.delete()
        self.client.logout()

        self.login(self.admin)
        # shouldn't be a report for nasho, 2010 yet
        self.assertEquals(0, Scorecard.objects.filter(wetmill=self.nasho, season=self.rwanda_2010).count())

        # check the list page, make sure our scorecard exists there
        response = self.client.get(reverse('scorecards.scorecard_list'))
        #self.assertEquals(1, len(response.context['scorecard_list']))
        #self.assertContains(response, self.nasho.name)

        self.setUpStandards()
        for standard in Standard.objects.all():
            self.rwanda_2010.standards.add(standard)

        scorecard = Scorecard.objects.create(wetmill=self.nasho, season=self.rwanda_2010, created_by=self.admin, modified_by=self.admin)
        standards_url = reverse('scorecards.scorecard_standards', args=[scorecard.id])
        response = self.client.get(standards_url)
        form_fields = response.context['form'].fields

        post_data = dict()
        for standard in Standard.objects.all():
            standard_key = 'standard__%d' % standard.id
            self.assertTrue(standard_key in form_fields)
            post_data[standard_key] = 100

        post_data['client_id'] = 'N/A'
        post_data['auditor'] = 'KEZA Ane'
        post_data['audit_date'] = "2011-11-11"

        self.assertPost(standards_url, post_data)

        standard_entries = scorecard.standard_entries.all()
        self.assertEquals(12, len(standard_entries))
        for entry in standard_entries:
            self.assertEqual(entry.value, 100)

        # make sure the values are shown on our read page
        response = self.client.get(reverse('scorecards.scorecard_read', args=[scorecard.id]))
        season_standards = response.context['season_standards']
        for season_standard in season_standards:
            self.assertEqual(season_standard.scorecard_value, standard_entries.get(standard=season_standard).value)

        # check initial values of the form
        response = self.client.get(standards_url)
        initials = response.context['form'].initial

        for standard in season_standards:
            standard_key = 'standard__%d' % standard.id
            self.assertEquals(initials[standard_key], 100)

        del post_data[standard_key]
        self.assertPost(standards_url, post_data)

        standard_entries = scorecard.standard_entries.all()
        self.assertEquals(11, len(standard_entries))

        # standard entry unicode
        self.assertEquals("%s - %s" % (standard_entries[0].standard.name, standard_entries[0].value),
                          str(standard_entries[0]))
        standard_entries[0].value = None
        standard_entries[0].save()
        self.assertEquals(standard_entries[0].standard.name, str(standard_entries[0]))

    def setUpStandardsForSeason(self, season):
        self.setUpStandards()
        season.add_standard(self.SRE1)
        season.add_standard(self.SRE2)
        season.add_standard(self.SRE3)
        season.add_standard(self.SRE4)

        season.add_standard(self.OHS1)
        season.add_standard(self.OHS2)
        season.add_standard(self.OHS3)
        season.add_standard(self.OHS4)

        season.add_standard(self.ER1)
        season.add_standard(self.ER2)
        season.add_standard(self.ER3)
        season.add_standard(self.ER4)

    def test_scorecard_finalize(self):

        # add standard to the season
        self.setUpStandardsForSeason(self.rwanda_2010)

        # create a scorecard
        scorecard = Scorecard.objects.create(season=self.rwanda_2010, wetmill=self.nasho,
                                             created_by=self.admin, modified_by=self.admin)

        # login
        self.login(self.admin)
        
        post_data = dict()
        finalize_url = reverse('scorecards.scorecard_finalize', args=[scorecard.id])
        read_url = reverse('scorecards.scorecard_read', args=[scorecard.id])

        # try to finalize the scorecard with all standards values empty
        response = self.assertPost(finalize_url, post_data)

        # should redirect to the read url
        self.assertAtURL(response, read_url)

        # with error message mentioning how unsuccessful the finalize operation was
        messages = [message for message in response.context['messages']]
        self.assertEqual(40, messages[0].level)
        # the length of the message tells it all
        self.assertGreater(len(messages), 0)
        self.assertFalse(scorecard.is_finalized)

        # add some standard entries
        standard_SRE1 = StandardEntry.objects.create(scorecard=scorecard, standard=self.SRE1, value="100", created_by=self.admin, modified_by=self.admin)
        standard_SRE2 = StandardEntry.objects.create(scorecard=scorecard, standard=self.SRE2, value="100", created_by=self.admin, modified_by=self.admin)
        standard_SRE3 = StandardEntry.objects.create(scorecard=scorecard, standard=self.SRE3, value="100", created_by=self.admin, modified_by=self.admin)
        standard_SRE4 = StandardEntry.objects.create(scorecard=scorecard, standard=self.SRE4, value="0", created_by=self.admin, modified_by=self.admin)

        # try to finalize the scorecard with half standard values empty
        response = self.assertPost(finalize_url, dict())

        # should redirect to the read url
        self.assertAtURL(response, read_url)

        # with error message mentioning how unsuccessful the finalize operation was
        messages = [message for message in response.context['messages']]
        self.assertEqual(40, messages[0].level)
        # the length of the message tells it all
        self.assertGreater(len(messages), 0)
        scorecard = Scorecard.objects.get(pk=scorecard.id)
        self.assertFalse(scorecard.is_finalized)

        # fill all remaining data
        standard_OHS1 = StandardEntry.objects.create(scorecard=scorecard, standard=self.OHS1, value="100", created_by=self.admin, modified_by=self.admin)
        standard_OHS2 = StandardEntry.objects.create(scorecard=scorecard, standard=self.OHS2, value="100", created_by=self.admin, modified_by=self.admin)
        standard_OHS3 = StandardEntry.objects.create(scorecard=scorecard, standard=self.OHS3, value="100", created_by=self.admin, modified_by=self.admin)
        standard_OHS4 = StandardEntry.objects.create(scorecard=scorecard, standard=self.OHS4, value="50", created_by=self.admin, modified_by=self.admin)        

        standard_ER1 = StandardEntry.objects.create(scorecard=scorecard, standard=self.ER1, value="100", created_by=self.admin, modified_by=self.admin)
        standard_ER2 = StandardEntry.objects.create(scorecard=scorecard, standard=self.ER2, value="100", created_by=self.admin, modified_by=self.admin)
        standard_ER3 = StandardEntry.objects.create(scorecard=scorecard, standard=self.ER3, value="100", created_by=self.admin, modified_by=self.admin)
        standard_ER4 = StandardEntry.objects.create(scorecard=scorecard, standard=self.ER4, value="90", created_by=self.admin, modified_by=self.admin)        

        # try to finalize the scorecard with all fields full
        response = self.assertPost(finalize_url, dict())        

        # should redirect to the read url
        self.assertAtURL(response, read_url)

        # the report has been finalized! Yey.
        messages = [message for message in response.context['messages']]
        self.assertEqual(25, messages[0].level)

        self.assertGreater(len(messages), 0)

        scorecard = Scorecard.objects.get(pk=scorecard.id)
        self.assertTrue(scorecard.is_finalized)

        # now that the report has been finalized any change after
        # will lead to amending

        # fill in the form only one field and let other empty
        post_dict = dict()
        post_dict['standard__%d' % self.OHS1.id] = 32
        
        standards_url = reverse('scorecards.scorecard_standards', args=[scorecard.id])
        response = self.client.post(standards_url, post_dict)

        # check if the amendment object has been created for this change
        # shouldn't cause there are many field which are empty
        self.assertIn('Unable to amend scorecard because the following fields are missing: ', response.content)

        # now add all values withing post_data
        post_dict['client_id'] = 'N/A'
        post_dict['auditor'] = 'KEZA Ane'
        post_dict['audit_date'] = "2011-11-11"

        post_dict['standard__%d' % self.SRE1.id] = 100
        post_dict['standard__%d' % self.SRE2.id] = 100
        post_dict['standard__%d' % self.SRE3.id] = 100
        post_dict['standard__%d' % self.SRE4.id] = 100

        post_dict['standard__%d' % self.OHS1.id] = 100
        post_dict['standard__%d' % self.OHS2.id] = 100
        post_dict['standard__%d' % self.OHS3.id] = 100
        post_dict['standard__%d' % self.OHS4.id] = 50

        post_dict['standard__%d' % self.ER1.id] = 100
        post_dict['standard__%d' % self.ER2.id] = 100
        post_dict['standard__%d' % self.ER3.id] = 100
        post_dict['standard__%d' % self.ER4.id] = 90

        response = self.assertPost(standards_url, post_dict)

        # now we have a success message 
        messages = [message for message in response.context['messages']]
        self.assertEqual(25, messages[0].level)

        # with amendment
        self.assertTrue(len(response.context['amendments']) > 0)

        # now generate the report for the sake of it
        self.client.get(reverse('scorecards.scorecard_pdf', args=[scorecard.id]))
        
        # test the rating of the scorecard
        # cause there is one of the minimum requirement which is no met the rating would be 'no_status'
        self.assertTrue(1, scorecard.get_rating())

        # now change the value to be met
        standard = scorecard.standard_entries.get(standard=self.SRE4)
        standard.value = 100
        standard.save()

        # the rating should be gold here
        self.assertEqual(5, scorecard.get_rating())

        # change standard_OHS1
        standard = scorecard.standard_entries.get(standard=self.OHS1)
        standard.value = 50
        standard.save()
        
        # the rating should be silver here
        self.assertEqual(4, scorecard.get_rating())

        # change standard_OHS1 and standard_OHS2
        standard = scorecard.standard_entries.get(standard=self.OHS1)
        standard.value = 0
        standard.save()

        standard = scorecard.standard_entries.get(standard=self.OHS2)
        standard.value = 50
        standard.save()

        # the rating should be bronze here
        self.assertEqual(3, scorecard.get_rating())        

        # change standard_OHS3
        standard = scorecard.standard_entries.get(standard=self.OHS3)
        standard.value = 0
        standard.save()

        # the rating should be bronze here
        self.assertTrue(2, scorecard.get_rating())

        # see if the scorecard comes back as a finalized scorecard
        self.assertIsNone(scorecard.wetmill.get_most_recent_scorecard())

        # but if we finalize the season
        season = scorecard.season
        season.is_finalized = True
        season.save()
        
        self.assertEquals(scorecard, scorecard.wetmill.get_most_recent_scorecard())
        
    def test_scorecard_pdf(self):

        # add standard to the season
        self.setUpStandardsForSeason(self.rwanda_2010)

        # create a scorecard
        scorecard = Scorecard.objects.create(season=self.rwanda_2010, wetmill=self.nasho,
                                             created_by=self.admin, modified_by=self.admin)

        # try to get a pdf report, remember this user haven't any permission
        self.login(self.viewer)
        response = self.client.get(reverse('scorecards.scorecard_pdf', args=[scorecard.id]))
        # should be redirected, you don't have permission fella..
        self.assertEquals(302, response.status_code)
        self.client.logout()

        # lets upgrade this user to be a viewer
        assign('wetmills.wetmill_report_view', self.viewer)
        self.login(self.viewer)
        response = self.client.get(reverse('scorecards.scorecard_pdf', args=[scorecard.id]))
        # it works!
        self.assertEquals(200, response.status_code)
        self.client.logout()

        # try again with a strong dude! Admin...
        self.login(self.admin)
        response = self.client.get(reverse('scorecards.scorecard_pdf', args=[scorecard.id]))
        # everybody! open the doors and pay respect to the admin
        self.assertEquals(200, response.status_code)
