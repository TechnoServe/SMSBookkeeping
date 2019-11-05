from scorecards.models import Scorecard, StandardEntry
from standards.models import Standard, StandardCategory
from tns_glass.scorecards.pdf.render import PDFScorecard
from tns_glass.tests import TNSTestCase
from decimal import Decimal

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class RenderTest(TNSTestCase):

    def setUp(self):
        super(RenderTest, self).setUp()
        self.scorecard = Scorecard.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        self.season = self.rwanda_2010
        self.nasho.set_csp_for_season(self.season, self.rtc)

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

    def render_scorecard(self):
        test_buffer = StringIO()
        pdf_scorecard = PDFScorecard(self.scorecard)
        pdf_scorecard.render(test_buffer)

        tmp_file = open('/tmp/scorecard.pdf', 'w')
        tmp_file.write(test_buffer.getvalue())
        tmp_file.close()

    def test_full_render(self):
        # add standard to the season
        self.setUpStandardsForSeason(self.rwanda_2010)

        # create a scorecard
        self.scorecard = Scorecard.objects.create(season=self.rwanda_2010, wetmill=self.nasho,
                                             created_by=self.admin, modified_by=self.admin)

        # add entries for all standards
        from datetime import datetime

        self.scorecard.auditor = "Joy Tushabe"
        self.scorecard.audit_date = datetime.today()

        # test break lines cover
        self.SRE1.name = 'NoChildLabourAnyWhereintheworldblablab'
        self.SRE1.save()

        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.SRE1, value=1, created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.SRE2, value="1", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.SRE3, value="1", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.SRE4, value="0", created_by=self.admin, modified_by=self.admin)

        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.OHS1, value="100", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.OHS2, value="100", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.OHS3, value="100", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.OHS4, value="50", created_by=self.admin, modified_by=self.admin)        

        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.ER1, value="1", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.ER2, value="1", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.ER3, value="0", created_by=self.admin, modified_by=self.admin)
        StandardEntry.objects.create(scorecard=self.scorecard, standard=self.ER4, value="10", created_by=self.admin, modified_by=self.admin)        
        
        # and finalize
        self.scorecard.is_finalized = True

        # and then render the scorecard
        self.render_scorecard()
