from django.test import TestCase
from django.conf import settings

from datetime import datetime,timedelta, date
from locales.models import Currency
import pytz

from rapidsms.models import Connection, Backend
from rapidsms.messages.incoming import IncomingMessage
from rapidsms_xforms.models import XForm
from rapidsms_httprouter.models import Message

from wetmills.models import Wetmill
from ..tests import TNSTestCase

from .models import *

from django.contrib.contenttypes.models import ContentType

from django.utils.translation import activate

class SMSTest(TNSTestCase):
    fixtures = ('test_auth', 'xforms', 'cc', 'twakinze', 'req_dates', 'day')

    def setUp(self):
        super(SMSTest, self).setUp()

        # fix up the reporter types for our CC message
        cc = MessageCC.objects.get(slug='amafaranga')
        cc.reporter_types.clear()
        cc.reporter_types.add(ContentType.objects.get(app_label="sms", model="wetmillobserver"))

        cc = MessageCC.objects.get(slug='ibitumbwe')
        cc.reporter_types.clear()
        cc.reporter_types.add(ContentType.objects.get(app_label="sms", model="wetmillobserver"))

        cc = MessageCC.objects.get(slug='sitoki')
        cc.reporter_types.clear()
        cc.reporter_types.add(ContentType.objects.get(app_label="sms", model="wetmillobserver"))

        cc = MessageCC.objects.get(slug='undo')
        cc.reporter_types.clear()
        cc.reporter_types.add(ContentType.objects.get(app_label="sms", model="wetmillobserver"))

        ccs = MessageCC.objects.filter(slug='obs')
        for cc in ccs:
            cc.reporter_types.clear()

        ccs = MessageCC.objects.filter(slug='acc')
        for cc in ccs:
            cc.reporter_types.clear()

        nasho = Wetmill.objects.get(name="Nasho")
        nasho.set_accounting_for_season(self.season, 'FULL')

        # change the end of our season to be in the future
        from dashboard.models import Assumptions
        assumptions = Assumptions.objects.get(season=self.season)
        assumptions.season_end = datetime.now() + timedelta(days=30)
        assumptions.save()

        self.backend = Backend.objects.create(name='tns')
        self.connection = Connection.objects.create(backend=self.backend, identity='250788123123')

        self.tz_backend = Backend.objects.create(name='tz')
        self.tz_connection = Connection.objects.create(backend=self.tz_backend, identity='255788123123')

        self.tsh = Currency.objects.create(name="Tanzanian Shillings",
                                           currency_code='TSH',
                                           abbreviation='TSH',
                                           has_decimals=True,
                                           prefix="",
                                           suffix="TSH",
                                           created_by=self.admin,
                                           modified_by=self.admin)

        self.tanzania = Country.objects.create(name="Tanzania",
                                               country_code='TZ',
                                               currency=self.tsh,
                                               weight=self.kilogram,
                                               calling_code='255',
                                               phone_format='#### ## ## ##',
                                               national_id_format='# #### # ####### # ##',
                                               bounds_zoom='6',
                                               bounds_lat='-1.333',
                                               bounds_lng='29.232',
                                               language='tz_sw',
                                               created_by=self.admin,
                                               modified_by=self.admin)

        # add a tanzanian wetmill
        self.izira = Wetmill.objects.create(name="Izira",
                                            country=self.tanzania,
                                            sms_name='izira',
                                            description="Izira Description",
                                            province=self.gitega,
                                            latitude = Decimal("-2.278038"),
                                            longitude = Decimal("30.643084"),
                                            altitude = Decimal("1479"),
                                            year_started=2008,
                                            created_by=self.admin,
                                            modified_by=self.admin)

        self.tz_season = Season.objects.create(name='2013',
                                               country=self.tanzania,
                                               exchange_rate=Decimal("585.00"),
                                               default_adjustment=Decimal("0.16"),
                                               farmer_income_baseline=Decimal("100"),
                                               fob_price_baseline="1.15",
                                               has_members=True,
                                               created_by=self.admin,
                                               modified_by=self.admin)

        assumptions = Assumptions.get_or_create(self.tz_season, None, None, self.admin)
        assumptions.season_start = date(day=1, month=1, year=2013)
        assumptions.season_end = datetime.today() + timedelta(days=30)
        assumptions.save()

    def tearDown(self):
        activate('en-us')

    def sms(self, number, text, success=True, response=None, backend=None):
        form = XForm.find_form(text)
        self.assertTrue(form)

        if not backend:
            backend, created = Backend.objects.get_or_create(name='tns')
        connection, created = Connection.objects.get_or_create(backend=backend, identity=number)

        message = IncomingMessage(connection, text)
        submission = form.process_sms_submission(message)

        if success:
            self.assertFalse(submission.has_errors, "SMS had errors: %s" % submission.response)
        else:
            self.assertTrue(submission.has_errors, "SMS did not have any errors: %s" % submission.response)

        if response:
            self.assertEquals(response, submission.response)

        return submission

    def test_farmer_registration(self):
        nasho = Wetmill.objects.get(name="Nasho")

        self.assertFalse(Farmer.objects.filter(wetmill=nasho).count())

        # register a farmer
        self.sms("1", "farmer nasho")

        farmers = Farmer.objects.filter(wetmill=nasho)
        self.assertEquals(1, farmers.count())
        self.assertEquals("1", farmers[0].connection.identity)

        # register as a farmer at coko
        self.sms("1", "farmer coko")
        coko = Wetmill.objects.get(name="Coko")

        self.assertFalse(Farmer.objects.filter(wetmill=nasho).count())

        farmers = Farmer.objects.filter(wetmill=coko)
        self.assertEquals(1, farmers.count())
        self.assertEquals("1", farmers[0].connection.identity)

        # register again at the same one
        self.sms("1", "farmer coko")
        coko = Wetmill.objects.get(name="Coko")

        # check that nothing has changed
        farmers = Farmer.objects.filter(wetmill=coko)
        self.assertEquals(1, farmers.count())
        self.assertEquals("1", farmers[0].connection.identity)

        # have them leave
        self.sms("1", "leave")

        self.assertFalse(Farmer.objects.filter(wetmill=nasho).count())
        self.assertFalse(Farmer.objects.filter(wetmill=coko).count())

    def test_accountant_registration(self):
        # get our wetmill
        wetmill = Wetmill.objects.get(name="Nasho")

        # register an accountant
        self.sms("1", "acc Nasho Eric Newcomer")

        acc1 = Accountant.for_wetmill(wetmill)
        self.assertEquals("Eric Newcomer", acc1.name)
        self.assertEquals("1", acc1.connection.identity)

        # should be able to reregister, just updates the name
        self.sms("1", "acc Nasho Eric")

        acc2 = Accountant.for_wetmill(wetmill)
        self.assertEquals("Eric", acc2.name)
        self.assertEquals("1", acc2.connection.identity)
        self.assertEquals(acc1.id, acc2.id)

        # but someone else should not be able to register for the same wetmill
        self.sms("2", "acc Nasho Nic", False)

        # should not have assigned a new accountant
        acc3 = Accountant.for_wetmill(wetmill)
        self.assertEquals(acc3.id, acc2.id)

        # have the first user unregister
        self.sms("1", "leave")

        # make sure there is now no accountant for the wetmill
        self.assertFalse(Accountant.for_wetmill(wetmill))

        # add an observer
        obs = self.sms("3", "obs Nasho Nic")

        # and try again
        self.sms("2", "acc Nasho Nic")

        acc3 = Accountant.for_wetmill(wetmill)
        self.assertEquals("Nic", acc3.name)
        self.assertEquals("2", acc3.connection.identity)

        # we don't do any cc's for acc registrations, but if we did it would show here
        msgs = Message.objects.filter(connection=obs.connection).order_by('-date')

    def test_language(self):
        self.sms("1", "acc Nasho Newcomer")

        acc = Accountant.objects.all()[0]
        self.assertEquals('rw', acc.language)

        sub = self.sms("1", "lang")

        # set it to english
        self.sms("1", "lang en")

        acc = Accountant.objects.all()[0]
        self.assertEquals('en-us', acc.language)

        # then back to kinyarwanda
        # set it to english
        self.sms("1", "lang rw")

        acc = Accountant.objects.all()[0]
        self.assertEquals('rw', acc.language)

        # try it with a cpo
        self.sms("2", "sc Nasho Newcomer")

        cpo = CPO.objects.get(name="Newcomer")
        self.assertEquals('rw', cpo.language)

        self.sms("2", "lang en")

        cpo = CPO.objects.get(name="Newcomer")
        self.assertEquals('en-us', cpo.language)

        # try it with an observer
        self.sms("3", "obs Nasho Newcomer")

        obs = WetmillObserver.objects.get(name="Newcomer")
        self.assertEquals('rw', obs.language)

        self.sms("3", "lang en")

        obs = WetmillObserver.objects.get(name="Newcomer")
        self.assertEquals('en-us', obs.language)

        # finally with csp
        self.sms("4", "csp RTC Newcomer")

        csp = CSPOfficer.objects.get(name="Newcomer")
        self.assertEquals('en-us', csp.language)

        self.sms("4", "lang rw")

        csp = CSPOfficer.objects.get(name="Newcomer")
        self.assertEquals('rw', csp.language)

    def test_lookup(self):
        self.sms("1", "acc Nasho Newcomer")

        sub = self.sms("1", "lookup")

        self.sms("2", "sc Nasho Eugene")
        self.sms("3", "sc Nasho Nic")

        self.sms("2", "lookup", False)

        sub = self.sms("1", "lookup")
        self.assertTrue('cpos' in sub.template_vars)

    def test_who(self):
        self.sms("1", "who", False)

        acc = self.sms("1", "acc Nasho Newcomer")
        msg = self.sms("1", "who")
        self.assertTrue("acc" in msg.template_vars)

        self.sms("2", "sc Nasho Pottier")
        msg = self.sms("2", "who")
        self.assertTrue("cpos" in msg.template_vars)

        msg = self.sms("2", "leave")
        self.sms("2", "who", False)

        self.sms("3", "obs Nasho Pottier")
        msg = self.sms("3", "who")
        self.assertTrue("obs" in msg.template_vars)

        msg = self.sms("3", "leave")
        self.sms("3", "who", False)

        self.sms("4", "csp rtc Pottier")
        msg = self.sms("4", "who")
        self.assertTrue("csp" in msg.template_vars)

        msg = self.sms("4", "leave")
        self.sms("4", "who", False)

    def test_daylot(self):
        tzname = settings.USER_TIME_ZONE
        tz = pytz.timezone(tzname)




        # after 8 PM, same day
        self.assertEquals("23.02.11", get_daylot(datetime(2011, 2, 23, 20, 0, 0, 0, tz).astimezone(pytz.utc)))

        # before 8 PM, previous day
        self.assertEquals("22.02.11", get_daylot(datetime(2011, 2, 23, 12, 0, 0, 0, tz).astimezone(pytz.utc)))

        # test parsing
        self.assertEquals("22.02.12", parse_daylot("foo", "22.02.12", connection=self.connection))
        self.assertEquals("22.02.12", parse_daylot("foo", "22.2.12", connection=self.connection))
        self.assertEquals("02.02.12", parse_daylot("foo", "2.2.12", connection=self.connection))

        # bad daylots
        try:
            self.assertEquals("blah", parse_daylot("foo", "222.02.11", connection=self.connection))
        except:
            pass

        try:
            self.assertEquals("blah", parse_daylot("foo", "22.02.1", connection=self.connection))
        except:
            pass

        try:
            self.assertEquals("blah", parse_daylot("foo", "aa.02.1", connection=self.connection))
        except:
            pass

    def test_observers(self):
        self.sms("1", "obs Nasho Newcomer")
        self.sms("2", "obs Coko Nicolas Pottier")
        self.sms("1", "obs Coko Newcomer")

        # make sure there are two observers for newcomer
        self.assertEquals(2, WetmillObserver.objects.filter(name="Newcomer").count())

        # two for coko
        self.assertEquals(2, WetmillObserver.objects.filter(wetmill__name="Coko").count())
        obs = WetmillObserver.objects.filter(wetmill__name="Coko").order_by('connection__identity')
        self.assertEquals("1", obs[0].connection.identity)
        self.assertEquals("2", obs[1].connection.identity)
        self.assertEquals("Nicolas Pottier", obs[1].name)

        # have one leave, this removes them from all, kinda lame but rare
        # that people will observe more than one anyways
        self.sms("1", "leave")

        self.assertEquals(0, WetmillObserver.objects.filter(wetmill__name="Nasho").count())
        self.assertEquals(1, WetmillObserver.objects.filter(wetmill__name="Coko").count())

        self.assertEquals("2", WetmillObserver.objects.filter(wetmill__name="Coko")[0].connection.identity)

        # test that at most a wetmill can have five observers
        self.sms("1", "obs Coko Eugene")
        self.sms("3", "obs Coko Eric")
        self.sms("4", "obs Coko Norbert")
        self.sms("5", "obs Coko Nic")

        # but that a third fails
        self.sms("6", "obs Coko Greg", False, "There are too many registered observers for the Coko wet mill.")

    def test_undo(self):
        self.nasho.set_accounting_for_season(self.season, 'LITE')

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # send in a report
        sub = self.sms("1", "sum 10 20 30 40 50")

        # ok, try to select that entry
        self.assertEquals(1, SummarySubmission.objects.filter(wetmill=self.nasho).count())

        # undo our message
        self.sms("1", "undo")

        # the entry should have been removed
        self.assertEquals(0, SummarySubmission.objects.filter(wetmill=self.nasho).count())

        # another undo should fail
        self.sms("1", "undo", False)

    def test_undo_window(self):
        acc = self.sms("1", "acc Nasho Newcomer")
        sub = self.sms("2", "sc Nasho Eugene")
        eugene_id = sub.confirmation_id
        msg = self.sms("1", "cherry %s 100 100 10 20000 500 5000 6000" % eugene_id)

        # push all of our submissions into the past
        window = timedelta(minutes=31)

        acc.created = sub.created - window
        acc.save()

        sub.created = sub.created - window
        sub.save()

        msg.created = msg.created - window
        msg.save()

        cpo = CPO.objects.get(cpo_id=eugene_id)

        # make sure that submission is there
        self.assertEquals(1, CherrySubmission.objects.filter(cpo=cpo).count())

        # undo shouldn't work since it was too long ago
        self.sms("1", "undo", False)

        # the entry should not have been removed
        self.assertEquals(1, CherrySubmission.objects.filter(cpo=cpo).count())

    def test_summary(self):
        # change nasho to be a LITE wetmill
        self.nasho.set_accounting_for_season(self.season, 'LITE')

        # if you aren't registered, doesn't work
        self.sms("1", "sum 10 10 10 10 10", False)

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # also register an observer
        obs = self.sms("2", "obs Nasho Eugene")

        # send in a report
        sub = self.sms("1", "sum 10 20 30 40 50")

        daylot = get_daylot(datetime.now(pytz.utc))

        self.assertEquals("Nasho", sub.template_vars['wetmill'].name)
        self.assertEquals(daylot, sub.template_vars['daylot'])
        self.assertEquals("2.0", str(sub.template_vars['avg_price']))

        # check that the submission got recorded
        summary = SummarySubmission.objects.get()
        self.assertEquals(daylot, summary.daylot)
        self.assertEquals(Wetmill.objects.get(name="Nasho"), summary.wetmill)
        self.assertEquals(10, summary.cherry)
        self.assertEquals(20, summary.paid)
        self.assertEquals(30, summary.stored)
        self.assertEquals(40, summary.sent)
        self.assertEquals(50, summary.balance)

        # check error cases
        self.sms("1", "sum asdf 10 10 10 10", False)
        self.sms("1", "sum 10 10 10 10", False)

        # try to send a cash message, that should fail, since this wetmill should be a LITE only
        self.sms("1", "cash 100000 0 0 0 0 0 0 0", False)


    def test_amafaranga(self):
        # try to send a message to nasho, should fail because we aren't an accountant
        msg = self.sms("1", "amafaranga 1000000 5000000 0 1000000 150000 6400 200000 400000 10000 20.1.12", False)
        self.assertTrue(msg.response.find("registered as accountant"))

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # add an observer
        obs = self.sms("2", "obs Nasho Eric")

        # now should fail because this wetmill isn't a 2012 wetmill
        msg = self.sms("1", "amafaranga 1000000 5000000 0 1000000 150000 6400 200000 400000 10000 20.1.12", False)
        self.assertTrue(msg.response.find("does not support this message"))

        # change nasho to a 2012 wetmill
        self.nasho.set_accounting_for_season(self.season, '2012')

        # should fail due to a missing date
        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000", False)
        self.assertTrue(msg.response.find("start date of"))

        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000 20.1.12")
        variables = msg.template_vars
        self.assertEquals("20,000", variables['opening_balance'])
        self.assertEquals("5,500", variables['cash_inflow'])
        self.assertEquals("15,900", variables['cash_outflow']) # 1000+1500+6400+2000+4000+1000
        self.assertEquals("9,600", variables['closing_balance'])
        self.assertEquals("0", variables['variance'])
        self.assertTrue(variables['week_end'])
        self.assertTrue(variables['week_start'])

        # should have no CC's yet
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # look up the AmafarangaSubmission
        sub = AmafarangaSubmission.all.get()

        # make sure it is not yet active
        self.assertFalse(sub.active)

        # check our values
        self.assertDecimalEquals("20000", sub.opening_balance)
        self.assertDecimalEquals("5000", sub.working_capital)
        self.assertDecimalEquals("500", sub.other_income)
        self.assertDecimalEquals("1000", sub.advanced)
        self.assertDecimalEquals("1500", sub.full_time_labor)
        self.assertDecimalEquals("6400", sub.casual_labor)
        self.assertDecimalEquals("2000", sub.commission)
        self.assertDecimalEquals("4000", sub.transport)
        self.assertDecimalEquals("1000", sub.other_expenses)

        # 'correct' the message
        msg = self.sms("1", "amafaranga 10000 5000 500 1000 1500 6400 2000 4000 1000 20.1.12")

        # still no CC
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # then commit it
        msg = self.sms("1", "OK")

        # finally the CC takes place
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())

        # should now have a single active one
        sub = AmafarangaSubmission.objects.get()

        self.assertTrue(sub.is_active)
        self.assertDecimalEquals("10000", sub.opening_balance)
        self.assertDecimalEquals("5000", sub.working_capital)
        self.assertDecimalEquals("500", sub.other_income)
        self.assertDecimalEquals("1000", sub.advanced)
        self.assertDecimalEquals("1500", sub.full_time_labor)
        self.assertDecimalEquals("6400", sub.casual_labor)
        self.assertDecimalEquals("2000", sub.commission)
        self.assertDecimalEquals("4000", sub.transport)
        self.assertDecimalEquals("1000", sub.other_expenses)

        ## double committing should have no difference
        msg = self.sms("1", "OK", False)
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())
        sub = AmafarangaSubmission.objects.get()

        # update the message
        msg = self.sms("1", "amafaranga 30000 5000 500 1000 1500 6400 2000 4000 1000 20.1.12")
        msg = self.sms("1", "OK")

        sub = AmafarangaSubmission.objects.get()
        self.assertDecimalEquals("30000", sub.opening_balance)

        # can still undo
        msg = self.sms("1", "undo")
        self.assertEquals(0, AmafarangaSubmission.objects.all().count())

        # remake it active, but move it to the previous week
        sub.active = True
        sub.start_of_week = sub.start_of_week - timedelta(days=7)
        sub.save()

        # now submit again, check for variance

        # closing balance before was 19,600, we are submitting with an opening of 20,000
        # should have a variance of -400
        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000 20.1.12")

        variables = msg.template_vars
        self.assertEquals("-400", variables['variance'])

        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000 20.01.12")
        variables = msg.template_vars
        self.assertEquals("20.01.12", variables['week_start'])
        self.assertEquals("26.01.12", variables['week_end'])

        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000 25.01.12")
        variables = msg.template_vars
        self.assertEquals("20.01.12", variables['week_start'])

        today = datetime.now()
        msg = self.sms("1", "amafaranga 20000 5000 500 1000 1500 6400 2000 4000 1000 %d.%d" % (today.day, today.month), False)
        self.assertTrue(msg.response.find("not yet complete") >= 0)

    def test_ibitumbwe(self):
        # try to send a message to nasho, should fail because we aren't an accountant
        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60 20.1.12", False)
        self.assertTrue(msg.response.find("registered as accountant"))

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # add an observer
        obs = self.sms("2", "obs Nasho Eric")

        # now should fail because this wetmill isn't a 2012 wetmill
        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60 12.01.12", False)
        self.assertTrue(msg.response.find("does not support this message"))

        # change nasho to a 2012 wetmill
        self.nasho.set_accounting_for_season(self.season, '2012')

        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60", False)
        self.assertTrue(msg.response.find("must include the date"))

        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60 12.01.12")
        variables = msg.template_vars
        self.assertEquals("60.00", variables['cherry_purchased'])
        self.assertEquals("100", variables['cherry_price'])
        self.assertEquals("3,000", variables['cash_balance'])
        self.assertEquals("12.01.12", variables['day'])

        # should have no CC's yet
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # look up the AmafarangaSubmission
        sub = IbitumbweSubmission.all.get()

        # make sure it is not yet active
        self.assertFalse(sub.active)

        # check our values
        self.assertDecimalEquals("10000", sub.cash_advanced)
        self.assertDecimalEquals("1000", sub.cash_returned)
        self.assertDecimalEquals("5000", sub.cash_spent)
        self.assertDecimalEquals("1000", sub.credit_spent)
        self.assertDecimalEquals("60", sub.cherry_purchased)

        # 'correct' the message
        msg = self.sms("1", "ibitumbwe 20000 1000 5000 1000 60 12.01.12")

        # try to undo the message before it is committed
        msg = self.sms("1", "undo", False)

        # still no CC
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # then commit it
        msg = self.sms("1", "ok")

        # finally the CC takes place
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())

        # should now have a single active one
        sub = IbitumbweSubmission.objects.get()

        self.assertDecimalEquals("20000", sub.cash_advanced)

        ## double committing should have no difference
        msg = self.sms("1", "ok", False)
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())
        sub = IbitumbweSubmission.objects.get()

        # send another
        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60 12.03.12")

        # check our balances, should take into account the previous message
        variables = msg.template_vars
        self.assertEquals("16,000", variables['cash_balance'])
        self.assertEquals("12.03.12", variables['day'])

        msg = self.sms("1", "OK")

        # clear our observer messages
        Message.objects.filter(connection=obs.connection).delete()

        # can still undo
        msg = self.sms("1", "undo")
        self.assertEquals(1, IbitumbweSubmission.objects.all().count())

        # observer should have received a message
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())
        self.assertTrue(Message.objects.get(connection=obs.connection).text.find("with keyword ibitumbwe cancelled"))

        # specify a date with a different format
        msg = self.sms("1", "ibitumbwe 10000 1000 5000 1000 60 12/1")

        # confirm it
        msg = self.sms("1", "OK")

        # should now have an entry for 12/1
        report_day = date(day=12, month=1, year=datetime.now().year)
        self.assertEquals(1, IbitumbweSubmission.objects.filter(report_day=report_day).count())
        self.assertTrue(IbitumbweSubmission.objects.get(report_day=report_day).is_active)

        # send another entry for the same date
        msg = self.sms("1", "ibitumbwe 10000 2000 5000 1000 60 12/1")

        # confirm it as well
        msg = self.sms("1", "OK")

        # should only have the new entry
        sub = IbitumbweSubmission.objects.get(report_day=report_day)
        self.assertEquals(Decimal("2000"), sub.cash_returned)

        # finally, submit a twakinze on that date
        msg = self.sms("1", "twakinze 12.1")
        msg = self.sms("1", "OK")

        self.assertFalse(IbitumbweSubmission.objects.filter(report_day=report_day))
        self.assertTrue(TwakinzeSubmission.objects.filter(report_day=report_day))

    def test_twakinze(self):
        # try to send a message to nasho, should fail because we aren't an accountant
        msg = self.sms("1", "twakinze 12.01.12", False)
        self.assertTrue(msg.response.find("registered as accountant"))

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # should fail, missing date
        msg = self.sms("1", "twakinze", False)
        self.assertTrue(msg.response.find("must include the date"))

        msg = self.sms("1", "twakinze 14.01.12", False)
        self.assertTrue(msg.response.find("does not support this message"))

        self.nasho.set_accounting_for_season(self.season, '2012')

        msg = self.sms("1", "twakinze 14.01.12")

        # no active entries yet
        self.assertFalse(TwakinzeSubmission.objects.all())

        # we need to send an ok to confirm
        msg = self.sms("1", "OK")

        twakinze = TwakinzeSubmission.objects.get()
        self.assertEquals(date(day=14, month=1, year=2012), twakinze.report_day)
        self.assertTrue(twakinze.active)
        self.assertTrue(twakinze.is_active)

        # try undoing
        msg = self.sms("1", "undo")
        self.assertFalse(TwakinzeSubmission.objects.all())

    def test_daily(self):
        # try to send a message to izira, should fail because we aren't an accountant
        msg = self.sms("1", "day 12.01.12 4014", False, backend=self.tz_backend)
        self.assertTrue(msg.response.find("registered as accountant"))

        # register as an accountant
        acc = self.sms("1", "acc izira Nicolas", backend=self.tz_backend)

        # should fail, missing date
        msg = self.sms("1", "day", False, backend=self.tz_backend)
        self.assertTrue(msg.response.find("must include the date"))

        # should fail, missing cherry
        msg = self.sms("1", "day 15.3.13", False, backend=self.tz_backend)
        self.assertTrue(msg.response.find("must include the cherry"))

        msg = self.sms("1", "day 15.3.13 500", False, backend=self.tz_backend)
        self.assertTrue(msg.response.find("does not support this message"))

        self.izira.set_accounting_for_season(self.season, 'LIT2')

        msg = self.sms("1", "day 15.3.13 500", backend=self.tz_backend)

        # no active entries yet
        self.assertFalse(IbitumbweSubmission.objects.all())

        # we need to send an ok to confirm
        msg = self.sms("1", "OK", backend=self.tz_backend)

        ibitumbwe = IbitumbweSubmission.objects.get()
        self.assertEquals(date(day=15, month=3, year=2013), ibitumbwe.report_day)
        self.assertEquals(self.tz_season, ibitumbwe.season)
        self.assertDecimalEquals(Decimal("500"), ibitumbwe.cherry_purchased)
        self.assertTrue(ibitumbwe.active)
        self.assertTrue(ibitumbwe.is_active)

        # try undoing
        msg = self.sms("1", "undo", backend=self.tz_backend)
        self.assertFalse(IbitumbweSubmission.objects.all())

    test_daily.active = True

    def test_sitoki(self):
        # try to send a message to nasho, should fail because we aren't an accountant
        msg = self.sms("1", "sitoki 1000 100 10 2000 200 20 20.1.12", False)
        self.assertTrue(msg.response.find("registered as accountant"))

        # register as an accountant
        acc = self.sms("1", "acc Nasho Nicolas")

        # add an observer
        obs = self.sms("2", "obs Nasho Eric")

        # now should fail because this wetmill isn't a 2012 wetmill
        msg = self.sms("1", "sitoki 1000 100 10 2000 200 20 20.1.12", False)
        self.assertTrue(msg.response.find("does not support this message"))

        # change nasho to a 2012 wetmill
        self.nasho.set_accounting_for_season(self.season, '2012')

        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # now should fail because it is missing a date
        msg = self.sms("1", "sitoki 1000 100 10 2000 200 20", False)
        self.assertTrue(msg.response.find("must include start"))

        three_weeks_ago = datetime.now() - timedelta(days=21)

        msg = self.sms("1", "sitoki 1000 200 20 1000 100 10 %d.%d" % (three_weeks_ago.day, three_weeks_ago.month))
        variables = msg.template_vars
        self.assertEquals("1,220", variables['total_stored'])
        self.assertEquals("1,110", variables['total_shipped'])
        self.assertEquals("110", variables['in_store'])
        self.assertTrue(variables['week_start'])
        self.assertTrue(variables['week_end'])

        # should have no CC's yet
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # look up the SitokiSubmission
        sub = SitokiSubmission.all.get()

        # make sure it is not yet active
        self.assertFalse(sub.active)

        # check our values
        self.assertDecimalEquals("1000", sub.grade_a_stored)
        self.assertDecimalEquals("200", sub.grade_b_stored)
        self.assertDecimalEquals("20", sub.grade_c_stored)
        self.assertDecimalEquals("1000", sub.grade_a_shipped)
        self.assertDecimalEquals("100", sub.grade_b_shipped)
        self.assertDecimalEquals("10", sub.grade_c_shipped)

        # 'correct' the message
        msg = self.sms("1", "sitoki 1000 200 22 1000 100 10 %d.%d" % (three_weeks_ago.day, three_weeks_ago.month))

        # still no CC
        self.assertEquals(0, Message.objects.filter(connection=obs.connection).count())

        # then commit it
        msg = self.sms("1", "ok")

        # finally the CC takes place
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())

        # should now have a single active one
        sub = SitokiSubmission.objects.get()

        self.assertTrue(sub.is_active)
        self.assertDecimalEquals("22", sub.grade_c_stored)

        ## double committing should have no difference
        msg = self.sms("1", "ok", False)
        self.assertEquals(1, Message.objects.filter(connection=obs.connection).count())
        sub = SitokiSubmission.objects.get()

        # update the message to three weeks ago
        msg = self.sms("1", "sitoki 2000 200 22 1000 100 10 %d.%d" % (three_weeks_ago.day, three_weeks_ago.month))
        msg = self.sms("1", "OK")

        sub = SitokiSubmission.objects.get()
        self.assertDecimalEquals("2000", sub.grade_a_stored)

        # send another for a week ago
        week_ago = datetime.now() - timedelta(days=7)
        msg = self.sms("1", "sitoki 2000 200 20 1000 100 10 %d.%d" % (week_ago.day, week_ago.month))

        # check our balances, should take into account the previous message
        variables = msg.template_vars
        self.assertEquals("2,222", variables['in_store'])

        msg = self.sms("1", "OK")
        self.assertEquals(2, SitokiSubmission.objects.all().count())

        # can still undo
        msg = self.sms("1", "undo")
        self.assertEquals(1, SitokiSubmission.objects.all().count())

        msg = self.sms("1", "sitoki 2000 200 20 1000 100 10 20.01.12")
        variables = msg.template_vars
        self.assertEquals("20.01.12", variables['week_start'])

        msg = self.sms("1", "sitoki 2000 200 20 1000 100 10 25/1/12")
        variables = msg.template_vars
        self.assertEquals("20.01.12", variables['week_start'])

        today = datetime.now()
        msg = self.sms("1", "sitoki 2000 200 20 1000 100 10 %d.%d" % (today.day, today.month), False)
        self.assertTrue(msg.response.find("not yet complete") >= 0)

    def test_week_start(self):
        self.assertEquals(date(day=20, month=1, year=2012),
                          get_week_start_before(date(day=27, month=1, year=2012)))

        self.assertEquals(date(day=20, month=1, year=2012),
                          get_week_start_before(date(day=28, month=1, year=2012)))

        self.assertEquals(date(day=20, month=1, year=2012),
                          get_week_start_before(date(day=31, month=1, year=2012)))

class ParsingTest(TNSTestCase):

    def setUp(self):
        super(ParsingTest, self).setUp()

        from django.contrib.sites.models import Site
        self.site = Site.objects.create(name="Test")

        self.backend = Backend.objects.create(name='tns')
        self.connection = Connection.objects.create(backend=self.backend, identity='250788123123')

    def assertFailure(self, day, today, error):
        try:
            parse_daylot("unused", day, today=today, connection=self.connection)
            self.fail("Should have thrown exception due to invalid format")
        except ValidationError as e:
            self.assertTrue(str(e).find(error) >= 0, "'%s' not found in error string: '%s'" % (error, str(e)))

    def test_daylot(self):
        # create our ibitumbwe form
        XForm.objects.create(name="Ibitumbwe Form", keyword='ibitumbwe', description="", response="response",
                             owner=self.admin, site=self.site)

        today = date(day=10, month=5, year=2012)
        self.assertEquals("09.05.12", parse_daylot("unused", "9.5", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "09.5", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "09.5.12", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "09.05", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "09/05", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "9/5", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "9/5/12", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "9/5/2012", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "9/05/2012", today=today, connection=self.connection))
        self.assertEquals("09.05.12", parse_daylot("unused", "09/05/2012", today=today, connection=self.connection))
        self.assertEquals("05.11.11", parse_daylot("unused", "05/11", today=today, connection=self.connection))

        self.assertFailure("31.2.12", today, "day you specified is not valid")
        self.assertFailure("33.5", today, "day you specified is not valid")
        self.assertFailure("28.15", today, "day you specified is not valid")
        self.assertFailure("1.1.14", today, "is in the future")
        self.assertFailure("1.1.01", today, "is too far in the past")
        self.assertFailure("1.asdf", today, "Invalid day format")

        today = date(day=10, month=10, year=2013)
        self.assertFailure("1.1.13", today, "season end date")
        
