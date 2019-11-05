from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from guardian.shortcuts import remove_perm, assign

from .models import *
from reports.models import Report
from scorecards.models import Scorecard

class PublicTestCase(TNSTestCase):

    def test_home(self):
        # first hit it without being logged in, should return a normal 200
        response = self.client.get(reverse('public-home'))
        self.assertEquals(200, response.status_code)

        # there should be a login link
        self.assertContains(response, reverse('users.user_login'))
        
        # but no admin menu, ie, no way of editing seasons say
        self.assertNotContains(response, reverse('seasons.season_list'))

        # once we log in however, we should have the menu
        self.login(self.admin)
        response = self.client.get(reverse('public-home'))
        self.assertEquals(200, response.status_code)

        # there should be a logout link
        self.assertContains(response, reverse('users.user_logout'))

        # but no login link
        self.assertNotContains(response, reverse('users.user_login'))

        # and our admin menu
        self.assertContains(response, reverse('seasons.season_list'))

    def test_country(self):
        # go check out rwanda as a country
        response = self.client.get(reverse('public-country', args=['rw']))

        # make sure some wetmills are listed
        self.assertContains(response, "Nasho")
        self.assertContains(response, "Coko")

        self.assertContains(response, reverse('public-wetmill', args=[self.nasho.id]))

    def test_wetmill(self):
        self.season = self.rwanda_2010
        self.report = Report.get_for_wetmill_season(self.nasho, self.season, self.viewer)
        self.scorecard = Scorecard.get_for_wetmill_season(self.nasho, self.season, self.viewer)

        # login with view report permission user
        self.login(self.viewer)
        response = self.client.get(reverse('public-wetmill', args=[self.nasho.id]))

        # nasho should be in the response
        self.assertContains(response, "Nasho")

        # check if the finalized report is inside the finalized list of report within the context
        # shouldn't be.
        self.assertFalse(self.report in response.context['finalized_reports'])
        self.assertFalse(self.report in response.context['finalized_scorecards'])
        
        # finalize on of this wetmills reports
        self.report.is_finalized = True
        self.report.save()

        # finalize the scorecard for this wetmill
        self.scorecard.is_finalized = True
        self.scorecard.save()

        response = self.client.get(reverse('public-wetmill', args=[self.nasho.id]))

        # nasho should be in the response
        self.assertContains(response, "Nasho")

        # check if the finalized report is inside the finalized list of report within the context
        self.assertTrue(self.report in response.context['finalized_reports'])
        self.assertTrue(self.scorecard in response.context['finalized_scorecards'])

        self.assertIsNone(response.context['last_scorecard'])
        self.assertIsNone(response.context['last_report'])

        # finalize the season
        self.season.is_finalized = True
        self.season.save()

        # get the page again
        response = self.client.get(reverse('public-wetmill', args=[self.nasho.id]))

        self.assertTrue(self.report in response.context['finalized_reports'])
        self.assertTrue(self.scorecard in response.context['finalized_scorecards'])

        self.assertEquals(self.scorecard, response.context['last_scorecard'])
        self.assertEquals(self.report, response.context['last_report'])

    def test_search(self):
        # first try a search without a query
        search_url = reverse('public-search')
        response = self.client.get(search_url + "?query=")

        # should return all wetmills (25 actually)
        self.assertContains(response, "Nasho")

        # now search specifically for nasho
        response = self.client.get(search_url + "?query=nasho")

        # response should be a redirect
        self.assertRedirect(response, reverse('public-wetmill', args=[self.nasho.id]))

        # search for nasho in kenya
        response = self.client.get(search_url + "?query=nasho&country=ke")

        # should have no results
        self.assertNotContains(response, "Nasho")
        self.assertEquals(0, response.context['wetmills'].count())

        # test something with multiple results
        response = self.client.get(search_url + "?query=o")
        self.assertContains(response, "Nasho")
        self.assertContains(response, "Coko")
        self.assertEquals(2, response.context['wetmills'].count())

    def test_counts(self):
        self.season = self.rwanda_2010
        self.report = Report.get_for_wetmill_season(self.nasho, self.season, self.viewer)
        self.report.farmers = 800
        self.report.is_finalized = True
        self.report.save()

        self.season.is_finalized = True
        self.season.save()

        self.assertEquals(800, get_total_farmers())
        self.assertEquals(800, get_total_farmers(self.rwanda))
        self.assertEquals(0, get_total_farmers(self.kenya))

        self.assertEquals(3, get_total_wetmills())
        self.assertEquals(1, get_total_wetmills(self.kenya))


