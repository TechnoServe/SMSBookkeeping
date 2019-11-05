from .models import *
from .tasks import *
from tns_glass.tests import TNSTestCase
from django.contrib.contenttypes.models import ContentType
from rapidsms_httprouter.models import Message

class ReminderTest(TNSTestCase):
    fixtures = ('test_auth', 'xforms', 'cc', 'twakinze')

    def setUp(self):
        super(ReminderTest, self).setUp()

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

        ccs = MessageCC.objects.filter(slug='obs')
        for cc in ccs:
            cc.reporter_types.clear()

        ccs = MessageCC.objects.filter(slug='acc')
        for cc in ccs:
            cc.reporter_types.clear()

    def tearDown(self):
        activate('en-us')

    def test_send_reminder(self):
        self.create_connections()
        self.season = self.rwanda_2010

        self.accountant = Accountant.objects.create(connection=self.conn1, name="Nic", wetmill=self.nasho)
        self.observer = WetmillObserver.objects.create(connection=self.conn2, name="Eric", wetmill=self.nasho)

        xform = XForm.objects.get(keyword='ibitumbwe')

        send_reminders_for_wetmills(xform, [self.nasho, self.coko], dict(greeting="Hello"), "{{greeting}}, the wetmill {{ wetmill.name }} is late.")

        # there should be two outgoing messages, one for the observer, one for the accountant
        outgoing = Message.objects.all()
        self.assertEquals(self.conn1, outgoing[0].connection)
        self.assertEquals("Hello, the wetmill Nasho is late.", outgoing[0].text)
        self.assertEquals(self.conn2, outgoing[1].connection)
        self.assertEquals("Hello, the wetmill Nasho is late.", outgoing[1].text)

    def test_reminder_wetmills(self):
        now = datetime.now()

        self.create_connections()
        self.season = self.rwanda_2010
        self.accountant = Accountant.objects.create(connection=self.conn1, name="Nic", wetmill=self.nasho)

        # ok, no messages have been sent yet, so we shouldn't get any reminders pending
        self.assertFalse(get_wetmills_needing_daily_reminder(now))
        self.assertFalse(get_wetmills_needing_weekly_reminder(now, AmafarangaSubmission.objects))
        self.assertFalse(get_wetmills_needing_weekly_reminder(now, SitokiSubmission.objects))

        four_days_ago = now - timedelta(days=4)

        # let's set an ibitumbwe message for a week ago, this shouldn't trigger our daily reminder
        # since it is too old, but should trigger our amafaranga and sitoki submissions
        ibitumbwe = IbitumbweSubmission.objects.create(accountant=self.accountant,
                                                       wetmill=self.nasho,
                                                       season=self.season,
                                                       report_day=four_days_ago,
                                                       cash_advanced=Decimal(0),
                                                       cash_returned=Decimal(0),
                                                       cash_spent=Decimal(0),
                                                       credit_spent=Decimal(0),
                                                       cherry_purchased=Decimal(0),
                                                       credit_cleared=Decimal(0))

        self.assertFalse(get_wetmills_needing_daily_reminder(now))
        self.assertEquals(set([self.nasho]), get_wetmills_needing_weekly_reminder(four_days_ago, AmafarangaSubmission.objects))
        self.assertEquals(set([self.nasho]), get_wetmills_needing_weekly_reminder(four_days_ago, SitokiSubmission.objects))

        # if we add an amafaranga submission recently, then it should no longer be an issue
        AmafarangaSubmission.objects.create(accountant=self.accountant,
                                            wetmill=self.nasho,
                                            season=self.season,
                                            start_of_week=four_days_ago,
                                            opening_balance=Decimal(0),
                                            working_capital=Decimal(0),
                                            other_income=Decimal(0),
                                            advanced=Decimal(0),
                                            full_time_labor=Decimal(0),
                                            casual_labor=Decimal(0),
                                            commission=Decimal(0),
                                            transport=Decimal(0),
                                            other_expenses=Decimal(0))

        self.assertFalse(get_wetmills_needing_daily_reminder(now))
        self.assertFalse(get_wetmills_needing_weekly_reminder(four_days_ago, AmafarangaSubmission.objects))
        self.assertEquals(set([self.nasho]), get_wetmills_needing_weekly_reminder(four_days_ago, SitokiSubmission.objects))

        # try sending our weekly messages
        check_weekly_reminders(now)

        # should be two messages that went out, one for sitoki, one for amafaranga
        msgs = Message.objects.all()
        self.assertEquals(2, len(msgs))
        self.assertTrue(msgs[0].text.find("Amafaranga") >= 0)
        self.assertEquals(self.conn1, msgs[0].connection)
        self.assertTrue(msgs[1].text.find("Sitoki") >= 0)
        self.assertEquals(self.conn1, msgs[1].connection)
        Message.objects.all().delete()

        # change our ibitumbwe message to be from a day ago instead
        ibitumbwe.report_day = now - timedelta(days=1)
        ibitumbwe.save()

        # nasho should now trigger as needing a daily message
        self.assertEquals(set([self.nasho]), get_wetmills_needing_daily_reminder(now))

        # check that our daily task does that (tomorrow)
        check_daily_reminders(now + timedelta(days=1))

        # should be one message sent out
        msgs = Message.objects.all()
        self.assertEquals(1, len(msgs))
        self.assertTrue(msgs[0].text.find("Ibitumbwe") >= 0)
        self.assertEquals(self.conn1, msgs[0].connection)
        Message.objects.all().delete()

        # but if there is a twakinze for that date it shouldn't
        TwakinzeSubmission.objects.create(accountant=self.accountant,
                                          wetmill=self.nasho,
                                          season=self.season,
                                          report_day=now)

        self.assertFalse(get_wetmills_needing_daily_reminder(now))

