from django.test import TestCase
from ..tests import TNSTestCase
from .models import *
from django.core.urlresolvers import reverse
import StringIO

class ScorecardImportTestCase(TNSTestCase):

    def setUp(self):
        super(ScorecardImportTestCase, self).setUp()

        self.add_standards()
        self.rwanda_2010.add_standard(self.child_labour)
        self.rwanda_2010.add_standard(self.forced_labour)
        self.rwanda_2010.add_standard(self.hazards)

    def assertLookupError(self, season, name, msg):
        try:
            lookup_standard(season, name)
            self.fail("Should have thrown error: %s" % msg)
        except Exception as e:
            if str(e).find(msg) < 0:
                self.fail("Should have thrown error: '%s', threw: '%s'" % (msg, str(e)))

    def test_lookup_standard(self):
        self.assertEquals(self.hazards, lookup_standard(self.rwanda_2010, "OHS - Work Place Hazards"))
        
        self.assertLookupError(self.rwanda_2010, "Work Place Hazards", "Invalid format for")
        self.assertLookupError(self.rwanda_2010, "DOH - Work Place Hazards", "Unable to find standards category")
        self.assertLookupError(self.rwanda_2010, "OHS - Work Place Huzards", "Unable to find standard")
        self.assertLookupError(self.rwanda_2010, "OHS - Safety Meetings", "Standard 'Safety Meetings' is not ")

    def assertParseError(self, standard, value, msg):
        try:
            parse_standard_value(standard, value)
            self.fail("Should have thrown error: %s" % msg)
        except Exception as e:
            if str(e).find(msg) < 0:
                self.fail("Should have thrown error: '%s', threw: '%s'" % (msg, str(e)))

    def test_parse_standard_value(self):
        self.assertEquals(100, parse_standard_value(self.hazards, " 100% "))
        self.assertEquals(100, parse_standard_value(self.hazards, "100%"))
        self.assertEquals(35, parse_standard_value(self.hazards, "35 %"))

        self.assertEquals(100, parse_standard_value(self.child_labour, "PASS"))
        self.assertEquals(100, parse_standard_value(self.child_labour, " pASs"))
        self.assertEquals(0, parse_standard_value(self.child_labour, " fail"))
        self.assertEquals(0, parse_standard_value(self.child_labour, "FAIL"))

        self.assertParseError(self.hazards, "PASS", "Invalid value")
        self.assertParseError(self.hazards, "105", "Invalid value")
        self.assertParseError(self.hazards, "-105", "Invalid value")
        self.assertParseError(self.hazards, "Asdf", "Invalid value")
        self.assertParseError(self.hazards, "", "Missing value")

        self.assertParseError(self.child_labour, "PASSED", "Invalid value")
        self.assertParseError(self.child_labour, "100%", "Invalid value")
        self.assertParseError(self.child_labour, "FAILED", "Invalid value")
        self.assertParseError(self.child_labour, "0", "Invalid value")
        self.assertParseError(self.child_labour, "", "Missing value")

    def assertBadImport(self, filename, error):
        path = self.build_import_path(filename)

        logger = StringIO.StringIO()
        try:
            reports = import_season_scorecards(self.season, path, self.admin, logger)
            self.fail("Should have thrown error")
        except Exception as e:
            self.assertTrue(e.message.find(error) == 0, "Should have found error: %s, instead found: %s" % (error, e.message))

    def test_import(self):
        logger = StringIO.StringIO()
        path = self.build_import_path("scorecard_import_1.csv")
        scorecards = import_season_scorecards(self.season, path, self.admin, logger)

        self.assertEquals(2, len(scorecards))
        self.assertEquals(self.nasho, scorecards[0].wetmill)
        self.assertEquals(self.coko, scorecards[1].wetmill)

        scorecard = Scorecard.objects.get(season=self.rwanda_2010, wetmill=self.nasho)
        self.assertEquals(None, scorecard.client_id)
        self.assertEquals("Eric Clapton", scorecard.auditor)
        self.assertEquals(datetime.date(2011, 6, 21), scorecard.audit_date)

        entries = scorecard.standard_entries.all()
        self.assertEquals(3, len(entries))
        self.assertEquals(self.child_labour, entries[0].standard)
        self.assertEquals(100, entries[0].value)

        self.assertEquals(self.forced_labour, entries[1].standard)
        self.assertEquals(0, entries[1].value)

        self.assertEquals(self.hazards, entries[2].standard)
        self.assertEquals(50, entries[2].value)

        scorecard = Scorecard.objects.get(season=self.rwanda_2010, wetmill=self.coko)
        self.assertEquals("CLIENT1", scorecard.client_id)

    def test_bad_imports(self):
        self.assertBadImport("scorecard_import_bad_wetmill.csv", "Unable to find wetmill")
        self.assertBadImport("scorecard_import_bad_standard.csv", "Unable to find standard")
        self.assertBadImport("scorecard_import_bad_value.csv", "Invalid value")
        self.assertBadImport("scorecard_import_bad_date.csv", "Invalid format for audit date")

    def test_views(self):
        response = self.client.get(reverse('scorecardimports.scorecardimport_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        # get a template for our season
        response = self.client.post(reverse('scorecardimports.scorecardimport_action'), 
                                    dict(template='template', season=self.season.id))
        self.assertEquals(200, response.status_code)
        self.assertTrue(response.content.find("Wet Mill,") == 0)

        # create a new import
        response = self.client.post(reverse('scorecardimports.scorecardimport_action'), 
                                    dict(create='create', season=self.season.id))
        self.assertRedirect(response, reverse('scorecardimports.scorecardimport_create'))

        create_url = response.get('Location', None)
        response = self.client.get(create_url)

        # should have a link to get our template
        self.assertContains(response, reverse('scorecardimports.scorecardimport_action'))

        # and mention our season
        self.assertContains(response, str(self.season))

        f = open(self.build_import_path("scorecard_import_1.csv"))
        post_data = dict(csv_file=f)
        response = self.assertPost(create_url, post_data)

        # make sure a new import was created
        scorecard_import = ScorecardImport.objects.get()
        self.assertEquals('PENDING', scorecard_import.get_status())
        self.assertEquals('CSV Import for Rwanda 2010', str(scorecard_import))
        self.assertEquals(self.season, scorecard_import.season)

        # while the scorecard is pending the read page should refresh
        self.assertEquals(2000, response.context['refresh'])

        scorecard_import.import_log = ""
        scorecard_import.save()
        scorecard_import.log("hello world")
        self.assertEquals("hello world\n", scorecard_import.import_log)

        # check out our list page
        response = self.client.get(reverse('scorecardimports.scorecardimport_list'))
        self.assertEquals(1, len(response.context['object_list']))
        self.assertContains(response, str(self.season))
        

        



        
