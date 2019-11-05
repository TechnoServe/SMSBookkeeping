from django.test import TestCase
from django.contrib.auth.models import User, Group
from locales.models import *
from expenses.models import *
from grades.models import *
from standards.models import *
from wetmills.models import *
from csps.models import *
from seasons.models import *
from django.core.urlresolvers import reverse
from urlparse import urlparse
from decimal import Decimal
from datetime import date, datetime
import os
from django.conf import settings
from rapidsms.models import Backend, Connection

class TNSTestCase(TestCase):

    def setUp(self):
        # no router, queue everything
        settings.ROUTER_URL = None

        if User.objects.filter(username='admin'):
            self.admin = User.objects.get(username='admin')
        else:
            self.admin = User.objects.create_user('admin', 'admin@admin.com', 'admin')

        self.admin.groups.add(Group.objects.get(name='Administrators'))
        self.viewer = User.objects.create_user('viewer', 'viewer@viewer.com', 'viewer')

        self.rwf = Currency.objects.create(name="Rwandan Francs",
                                           currency_code='RWF',
                                           abbreviation='RWF',
                                           has_decimals=False,
                                           prefix="",
                                           suffix=" RWF",
                                           created_by=self.admin,
                                           modified_by=self.admin)

        self.usd = Currency.objects.create(name="US Dollars",
                                           currency_code='USD',
                                           abbreviation='US$',
                                           has_decimals=True,
                                           prefix="$",
                                           suffix="",
                                           created_by=self.admin,
                                           modified_by=self.admin)
        self.kilogram = Weight.objects.create(name="Kilograms",
                                              abbreviation="Kg",
                                              ratio_to_kilogram="1",
                                              created_by=self.admin,
                                              modified_by=self.admin)
        self.metric_tons = Weight.objects.create(name="Metric Tons",
                                                 abbreviation="mT",
                                                 ratio_to_kilogram="1000",
                                                 created_by=self.admin,
                                                 modified_by=self.admin)


        self.rwanda = Country.objects.create(name="Rwanda",
                                             country_code='RW',
                                             currency=self.rwf,
                                             weight=self.kilogram,
                                             calling_code='250',
                                             phone_format='#### ## ## ##',
                                             national_id_format='# #### # ####### # ##',
                                             bounds_zoom='6',
                                             bounds_lat='-1.333',
                                             bounds_lng='29.232',
                                             language='rw',
                                             created_by=self.admin,
                                             modified_by=self.admin)

        self.ksh = Currency.objects.create(name="Kenyan Shillings",
                                           currency_code='KSH',
                                           has_decimals=False,
                                           prefix="",
                                           suffix=" KSH",
                                           created_by=self.admin,
                                           modified_by=self.admin)

        self.kenya = Country.objects.create(name="Kenya",
                                            country_code='KE',
                                            currency=self.ksh,
                                            weight=self.kilogram,
                                            calling_code='254',
                                            phone_format='#### ## ## ##',
                                            national_id_format='# #### # ####### # ##',
                                            bounds_zoom='6',
                                            bounds_lat='-1.333',
                                            bounds_lng='29.232',
                                            language='ke_sw',
                                            created_by=self.admin,
                                            modified_by=self.admin)

        self.gitega = Province.objects.create(name="Gitega",
                                              country=self.rwanda,
                                              order=1,
                                              created_by=self.admin,
                                              modified_by=self.admin)

        self.bwanacyambwe = Province.objects.create(name="Bwanacyambwe",
                                                    country=self.rwanda,
                                                    order=2,
                                                    created_by=self.admin,
                                                    modified_by=self.admin)

        self.kibirira = Province.objects.create(name="Kibirira",
                                                country=self.kenya,
                                                order=1,
                                                created_by=self.admin,
                                                modified_by=self.admin)                                                

        self.mucoma = Province.objects.create(name="Mucoma",
                                              country=self.kenya,
                                                order=2,
                                                created_by=self.admin,
                                                modified_by=self.admin)


        # add a couple csp's to Rwanda
        self.rtc = CSP.objects.create(name="Rwanda Trading Company", 
                                      sms_name="rtc",
                                      country=self.rwanda,
                                      description="Rwanda Trading Company",
                                      created_by=self.admin,
                                      modified_by=self.admin)

        self.wetu = CSP.objects.create(name="Wetu",
                                       sms_name="wetu",
                                       country=self.kenya,
                                       created_by=self.admin,
                                       modified_by=self.admin)

        self.rwacof = CSP.objects.create(name="Rwacof",
                                         sms_name="rwacof",
                                         country=self.rwanda,
                                         description="Rwacof",
                                         created_by=self.admin,
                                         modified_by=self.admin)

        # and some wetmills
        self.nasho = Wetmill.objects.create(name="Nasho",
                                            country=self.rwanda,
                                            sms_name='nasho',
                                            description="Nasho Description",
                                            province=self.gitega,
                                            latitude = Decimal("-2.278038"),
                                            longitude = Decimal("30.643084"),
                                            altitude = Decimal("1479"),
                                            year_started=2008,
                                            created_by=self.admin,
                                            modified_by=self.admin)

        self.coko = Wetmill.objects.create(name="Coko",
                                           country=self.rwanda,
                                           sms_name='coko',
                                           description="Coko Description",
                                           province=self.bwanacyambwe,
                                           year_started=2009,
                                            created_by=self.admin,
                                           modified_by=self.admin)

        self.kaguru = Wetmill.objects.create(name="Kaguru",
                                             country=self.kenya,
                                             sms_name='Kaguru',
                                             description="Kaguru Description",
                                             province=self.mucoma,
                                             year_started=2010,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        self.rwanda_2009 = Season.objects.create(name='2009',
                                                 country=self.rwanda,
                                                 exchange_rate=Decimal("585.00"),
                                                 default_adjustment=Decimal("0.16"),
                                                 has_members=True,
                                                 farmer_income_baseline=Decimal("100"),
                                                 fob_price_baseline="1.15",
                                                 created_by=self.admin,
                                                 modified_by=self.admin)

        self.rwanda_2010 = Season.objects.create(name='2010',
                                                 country=self.rwanda,
                                                 exchange_rate=Decimal("585.00"),
                                                 default_adjustment=Decimal("0.16"),
                                                 has_members=True,
                                                 farmer_income_baseline=Decimal("100"),
                                                 fob_price_baseline=Decimal("1.15"),
                                                 sale_price_left=Decimal("10"),
                                                 sale_price_right=Decimal("20"),
                                                 created_by=self.admin,
                                                 modified_by=self.admin)

        self.nasho.set_accounting_for_season(self.rwanda_2009, '2012')
        self.nasho.set_accounting_for_season(self.rwanda_2010, '2012')

        self.kenya_2011 = Season.objects.create(name='2011',
                                                country=self.kenya,
                                                exchange_rate=Decimal("585.00"),
                                                default_adjustment=Decimal("0.16"),
                                                farmer_income_baseline=Decimal("100"),
                                                fob_price_baseline="1.15",
                                                has_members=True,
                                                created_by=self.admin,
                                                modified_by=self.admin)

        self.season = self.rwanda_2010

        from dashboard.models import Assumptions
        season_assumptions = Assumptions.get_or_create(self.season, None, None, self.admin)
        season_assumptions.season_start = date(day=1, month=11, year=2011)
        season_assumptions.season_end = date(day=1, month=10, year=2012)
        season_assumptions.save()

        self.sre_category = StandardCategory.objects.create(name="Social Responsibility & Ethics",
                                                            acronym="SRE",
                                                            order=1,
                                                            created_by=self.admin, 
                                                            modified_by=self.admin)

        self.ohs_category = StandardCategory.objects.create(name="Occupational Health & Safety", 
                                                            acronym="OHS",
                                                            order=20,
                                                            created_by=self.admin, 
                                                            modified_by=self.admin)

    def add_expenses(self):
        self.expense_washing_station = Expense.objects.create(name="Washing Station Expenses", order=1,
                                                              created_by=self.admin, modified_by=self.admin)

        self.expense_other = Expense.objects.create(name="Other Expenses", order=2, parent=self.expense_washing_station,
                                                    created_by=self.admin, modified_by=self.admin)

        self.expense_cherry_advance = Expense.objects.create(name="Cherry Advance", order=1, is_advance=True,
                                                             parent=self.expense_washing_station,
                                                             created_by=self.admin, modified_by=self.admin)

        self.expense_taxes = Expense.objects.create(name="Taxes", order=1, parent=self.expense_other,
                                                    created_by=self.admin, modified_by=self.admin)

        self.expense_unexplained = Expense.objects.create(name="Unexplained", order=2, parent=self.expense_other,
                                                          created_by=self.admin, modified_by=self.admin)

        self.expense_capex = Expense.objects.create(name="CAPEX Financing Expenses", order=3, in_dollars=True,
                                                    created_by=self.admin, modified_by=self.admin)

        self.expense_capex_interest = Expense.objects.create(name="Capex Interest", order=0, parent=self.expense_capex, in_dollars=True,
                                                             created_by=self.admin, modified_by=self.admin)

    def add_grades(self):
        self.cherry = self.add_grade("Cherry", 'CHE', 0)
        self.parchment = self.add_grade("Parchment", 'PAR', 1)
        self.green = self.add_grade("Green", 'GRE', 3)
        self.green15 = self.add_grade("Screen 15+", 'GRE', 0, self.green)
        self.green13 = self.add_grade("Screen 13,14", 'GRE', 1, self.green)
        self.low = self.add_grade("Low Grades", 'GRE', 2, self.green)
        self.ungraded = self.add_grade("Ungraded", 'GRE', 1, self.low)

    def add_standards(self):
        self.child_labour = Standard.objects.create(name="No Child Labour", category=self.sre_category, 
                                                    kind="MR", order=1, created_by=self.admin, modified_by=self.admin)
        self.forced_labour = Standard.objects.create(name="No Forced Labour", category=self.sre_category, 
                                                    kind="MR", order=2, created_by=self.admin, modified_by=self.admin)
        self.meetings = Standard.objects.create(name="Safety Meetings", category=self.ohs_category, 
                                                     kind="MR", order=1, created_by=self.admin, modified_by=self.admin)
        self.hazards = Standard.objects.create(name="Work Place Hazards", category=self.ohs_category, 
                                               kind="BP", order=2, created_by=self.admin, modified_by=self.admin)

    def add_cash_sources(self):
        self.unused_working_cap = CashSource.objects.create(name="Unused Working Capital", order=1, calculated_from='WCAP', 
                                                            created_by=self.admin, modified_by=self.admin)

    def add_farmer_payments(self):
        self.fp_dividend = FarmerPayment.objects.create(name="Dividend", order=0,
                                                        created_by=self.admin, modified_by=self.admin)
        self.fp_second_payment = FarmerPayment.objects.create(name="Second Payment", order=1,
                                                           created_by=self.admin, modified_by=self.admin)

    def add_cash_uses(self):
        self.cu_dividend = CashUse.objects.create(name="Dividend", order=0,
                                                  created_by=self.admin, modified_by=self.admin)
        self.cu_second_payment = CashUse.objects.create(name="Second Payment", order=1,
                                                        created_by=self.admin, modified_by=self.admin)

    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password=user.username))

    def assertPost(self, url, post_data):
        response = self.client.post(url, post_data, follow=True)
        self.assertEquals(200, response.status_code, "Post got a non 200 response code.  Got %d instead." % response.status_code)
        self.assertTrue(not 'form' in response.context, "Post response had form within it.")
        return response

    def assertAtURL(self, response, url):
        self.assertEquals(response.request['PATH_INFO'], url,
                        "At url: %s instead of %s" % (response.request['PATH_INFO'], url))

    def assertRedirect(self, response, url):
        self.assertEquals(302, response.status_code)
        segments = urlparse(response.get('Location', None))
        self.assertEquals(segments.path, url)

    def assertInitial(self, response, field, value):
        self.assertTrue('form' in response.context)
        form = response.context['form']
        self.assertTrue(field in form.initial)
        self.assertEquals(value, form.initial[field])

    def add_grade(self, name, kind, order, parent=None):
        return Grade.objects.create(name=name, kind=kind, order=order, parent=parent,
                                    created_by=self.admin, modified_by=self.admin)

    def assertDecimalEquals(self, truth, test):
        """ asserts the two values are the same to within two decimal places """
        from decimal import ROUND_HALF_UP

        truth_rounded = Decimal(truth).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        test_rounded = Decimal(str(test)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        self.assertEquals(truth_rounded, test_rounded)

    def add_expense(self, parent, name, value=None, exchange_rate=None):
        """
        Test utility method that creates an expense, adds it to the season and also adds the passed in
        value for our report object
        """
        order = Expense.objects.filter(parent=parent).count() + 1
        
        # create the expense
        expense = Expense.objects.create(parent=parent, name=name, order=order, 
                                         created_by=self.admin, modified_by=self.admin)

        # add it to our season
        self.season.add_expense(expense)

        # if we have a value, add the value as an entry for our report
        if value:
            self.report.expenses.create(expense=expense, value=Decimal(value), exchange_rate=exchange_rate,
                                        created_by=self.admin, modified_by=self.admin)

        return expense

    def add_standard(self, name, category, kind, order, value):
        """
        Test utility method that creates a standard, adds it to the season and also adds the passed in
        value for our report object
        """
        standard = Standard.objects.create(name=name, category=category, kind=kind, order=order)
        
        self.season.add_standard(standard)

        if value:
            self.scorecard.standards.create(standard=standard, value=Decimal(value), created_by=self.admin, modified_by=self.admin)

        return standard

    def build_import_path(self, name):
        return os.path.join(settings.TESTFILES_DIR, name)

    def generate_report(self, wetmill, multiplier):
        from reports.models import Report, ExpenseEntry, Production, CashUseEntry, FarmerPaymentEntry

        self.season.exchange_rate = Decimal("600")
        self.season.save()

        report = Report.get_for_wetmill_season(wetmill, self.season, self.admin)

        for expense in (self.expense_cherry_advance, self.expense_taxes):
            ExpenseEntry.objects.create(report=report, expense=expense,
                                        value=Decimal("10000") * multiplier, exchange_rate=None,
                                        created_by=self.admin, modified_by=self.admin)

        ExpenseEntry.objects.create(report=report, expense=self.expense_capex_interest,
                                    value=Decimal("3") * multiplier, exchange_rate=Decimal("500"),
                                    created_by=self.admin, modified_by=self.admin)

        Production.objects.create(report=report, grade=self.cherry, volume=Decimal("1000"), 
                                  created_by=self.admin, modified_by=self.admin)

        Production.objects.create(report=report, grade=self.parchment, volume=Decimal("500"), 
                                  created_by=self.admin, modified_by=self.admin)

        Production.objects.create(report=report, grade=self.green15, volume=Decimal("300"), 
                                  created_by=self.admin, modified_by=self.admin)

        Production.objects.create(report=report, grade=self.green13, volume=Decimal("200"), 
                                  created_by=self.admin, modified_by=self.admin)

        CashUseEntry.objects.create(report=report, cash_use=self.cu_dividend, 
                                    value=Decimal("10000") * multiplier, 
                                    created_by=self.admin, modified_by=self.admin)

        FarmerPaymentEntry.objects.create(report=report, farmer_payment=self.fp_dividend,
                                    member_per_kilo=Decimal("100") * multiplier,
                                    created_by=self.admin, modified_by=self.admin)

        CashUseEntry.objects.create(report=report, cash_use=self.cu_second_payment, 
                                    value=Decimal("15000") * multiplier, 
                                    created_by=self.admin, modified_by=self.admin)

        FarmerPaymentEntry.objects.create(report=report, farmer_payment=self.fp_second_payment,
                                          member_per_kilo=Decimal("150") * multiplier,
                                          non_member_per_kilo=Decimal("150") * multiplier,
                                          created_by=self.admin, modified_by=self.admin)

        report.is_finalized = True
        report.save()

        return report

    def configure_season(self):
        self.add_expenses()
        self.add_grades()
        self.add_cash_uses()
        self.add_farmer_payments()

        SeasonExpense.objects.filter(season=self.season).delete()
        SeasonGrade.objects.filter(season=self.season).delete()
        
        self.season.cash_uses.clear()
        self.season.cash_sources.clear()
        self.season.farmer_payments.all().delete()

        # add a few expenses
        self.season.add_expense(self.expense_washing_station)
        self.season.add_expense(self.expense_cherry_advance)
        self.season.add_expense(self.expense_other)
        self.season.add_expense(self.expense_taxes)
        self.season.add_expense(self.expense_capex)
        self.season.add_expense(self.expense_capex_interest)

        # and a few grades
        self.season.add_grade(self.cherry)
        self.season.add_grade(self.parchment)
        self.season.add_grade(self.green)
        self.season.add_grade(self.green15)
        self.season.add_grade(self.green13)

        # add a few cash uses
        self.season.add_cash_use(self.cu_dividend)
        self.season.add_cash_use(self.cu_second_payment)
        
        self.season.add_farmer_payment(self.fp_dividend, 'MEM')
        self.season.add_farmer_payment(self.fp_second_payment, 'BOT')

        self.nasho.set_accounting_for_season(self.season, '2012')
        self.coko.set_accounting_for_season(self.season, '2012')

    def create_connections(self):
        (test, created) = Backend.objects.get_or_create(name="test")
        (self.conn1, created) = Connection.objects.get_or_create(backend=test, identity='1')
        (self.conn2, created) = Connection.objects.get_or_create(backend=test, identity='2')
        (self.conn3, created) = Connection.objects.get_or_create(backend=test, identity='3')



