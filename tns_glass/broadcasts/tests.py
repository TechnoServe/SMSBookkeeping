from django.test import TestCase
from ..tests import TNSTestCase
from .models import Broadcast
from django.core.urlresolvers import reverse
from wetmills.models import WetmillCSPSeason
import datetime

from rapidsms.models import Backend, Connection
from sms.models import Farmer, Accountant, WetmillObserver, SitokiSubmission, AmafarangaSubmission, IbitumbweSubmission, get_week_start_before
from decimal import Decimal
from reports.models import Report
from aggregates.models import ReportValue, SeasonAggregate

class BroadcastTestCase(TNSTestCase):

    def test_broadcasts(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()

        # create a new broadcast
        broadcast = Broadcast.objects.create(recipients='F',
                                             text="This is my test message",
                                             country=self.rwanda,
                                             report_season=self.season,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("2"))
        SeasonAggregate.calculate_for_season(self.season)

        # make sure RTC is the CSP for nasho in 2010
        WetmillCSPSeason.objects.create(wetmill=self.nasho,
                                        csp=self.rtc,
                                        season=self.season)

        # should return both rwanda wetmills
        wetmills = broadcast.get_wetmills()
        self.assertEquals(2, len(wetmills))
        self.assertEquals(self.coko, wetmills[0])
        self.assertEquals(self.nasho, wetmills[1])

        # restrict to RTC
        broadcast.csps.add(self.rtc)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(1, len(broadcast.get_wetmills()))
        self.assertEquals(self.nasho, wetmills[0])

        # restrict to just nasho
        broadcast.wetmills.add(self.nasho)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(1, len(wetmills))
        self.assertEquals(self.nasho, wetmills[0])

    def test_sms_render(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()
        
        broadcast = Broadcast.objects.create(recipients='F',
                                             text="",
                                             country=self.rwanda,
                                             sms_season=self.season,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        accountant = Accountant.objects.create(connection=self.conn2, name="Nic", wetmill=self.nasho)

        broadcast.text = "{{sms_cherry_purchased}} {{sms_parchment_processed}} {{sms_cherry_to_parchment_ratio}} {{ sms_working_cap }} {{ sms_working_cap_non_cherry_percent }} {{ sms_casual_labor_kgc }} {{ last_ibitumbwe_submission|date:'j/n/y' }} {{ last_sitoki_submission|date:'j/n/y' }} {{ last_amafaranga_submission|date:'j/n/y' }} {{ today|date:'j/n/y' }}"
        broadcast.save()

        now = datetime.datetime(day=19, month=1, year=2013, hour=15, minute=30)

        self.assertEquals(0, len(broadcast.get_wetmills()))

        self.assertEquals("0 0 0 0 0 0    19/1/13", broadcast.render(self.nasho, accountant, now))

        # get the start of the week
        today = datetime.date(day=19, month=1, year=2013)
        previous_week = datetime.date(day=11, month=1, year=2013)
        start_of_week = datetime.date(day=18, month=1, year=2013)

        today_minus_11 = datetime.date(day=8, month=1, year=2013)
        today_minus_5 =  datetime.date(day=14, month=1, year=2013)

        # create our sms messages for nasho
        AmafarangaSubmission.objects.create(accountant=accountant,
                                            wetmill=self.nasho,
                                            season=self.season,
                                            active=True,
                                            start_of_week=start_of_week,
                                            opening_balance=Decimal(0),
                                            working_capital=Decimal(1000),
                                            other_income=Decimal(0),
                                            advanced=Decimal(0),
                                            full_time_labor=Decimal(100),
                                            casual_labor=Decimal(100),
                                            commission=Decimal(100),
                                            transport=Decimal(100),
                                            other_expenses=Decimal(100))
        
        IbitumbweSubmission.objects.create(accountant=accountant,
                                           wetmill=self.nasho,
                                           season=self.season,
                                           report_day=today_minus_11,
                                           active=True,
                                           cash_advanced=Decimal(0),
                                           cash_returned=Decimal(0),
                                           cash_spent=Decimal(0),
                                           credit_spent=Decimal(0),
                                           cherry_purchased=Decimal(100),
                                           credit_cleared=Decimal(0))

        IbitumbweSubmission.objects.create(accountant=accountant,
                                           wetmill=self.nasho,
                                           season=self.season,
                                           report_day=today_minus_5,
                                           active=True,
                                           cash_advanced=Decimal(0),
                                           cash_returned=Decimal(0),
                                           cash_spent=Decimal(0),
                                           credit_spent=Decimal(0),
                                           cherry_purchased=Decimal(10),
                                           credit_cleared=Decimal(0))

        SitokiSubmission.objects.create(accountant=accountant,
                                        wetmill=self.nasho,
                                        season=self.season,
                                        start_of_week=start_of_week,
                                        active=True,
                                        grade_a_stored=Decimal(50),
                                        grade_b_stored=Decimal(0),
                                        grade_c_stored=Decimal(20),
                                        grade_a_shipped=Decimal(0),
                                        grade_b_shipped=Decimal(0),
                                        grade_c_shipped=Decimal(0))

        self.assertEquals("100.00 70.00 1.43 1000.00 50 0.91 14/1/13 18/1/13 18/1/13 19/1/13", broadcast.render(self.nasho, accountant, now))

        self.assertEquals(1, len(broadcast.get_wetmills()))

    def test_render(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()

        self.nasho.set_csp_for_season(self.season, self.rtc)
        self.coko.set_csp_for_season(self.season, self.rwacof)
        
        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("2"))

        broadcast = Broadcast.objects.create(recipients='F',
                                             text="",
                                             country=self.rwanda,
                                             report_season=self.season,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(0, len(wetmills))

        SeasonAggregate.calculate_for_season(self.season)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(2, len(wetmills))

        # exclude a wetmill
        broadcast.exclude_wetmills.add(self.coko)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(1, len(wetmills))
        self.assertEquals(self.nasho, wetmills[0])

        # back to what we had but add in a csp
        broadcast.exclude_wetmills.remove(self.coko)
        broadcast.exclude_csps.add(self.rtc)

        wetmills = broadcast.get_wetmills()
        self.assertEquals(1, len(wetmills))
        self.assertEquals(self.coko, wetmills[0])
        
        # reset
        broadcast.exclude_csps.remove(self.rtc)

        accountant = Accountant.objects.create(connection=self.conn2, name="Nic", wetmill=self.nasho)

        broadcast.text = "{{unknown_field}} {{wetmill.name}} {{actor.name}}"
        broadcast.save()

        now = datetime.datetime.now()

        self.assertEquals("Nasho Nic", broadcast.render(self.nasho, accountant, now))

        # have some real values from the transparency report
        broadcast.text = "{{total_expenses|floatformat:0}} {{total_expenses__rank}}/{{ total_wetmills }}"
        broadcast.save()

        self.assertEquals("21800 1/2", broadcast.render(self.nasho, accountant, now))

        # try an if statement, make sure we strip spaces out
        broadcast.text = "{% if total_expenses < 0 %}This won't be shown{%endif%}  "
        broadcast.save()
        self.assertEquals("", broadcast.render(self.nasho, accountant, now))

        # things shouldnt blow up too bad either
        try:
            broadcast.text = "{% if total_expenses asdfa 0 %}This won't be shown{%endif%}  "
            broadcast.save()
            broadcast.render(self.nasho, accountant, now)
            fail("Should have thrown exception")
        except:
            pass

    def test_recipients(self):
        self.create_connections()

        broadcast = Broadcast.objects.create(recipients='F',
                                             text="This is my test message",
                                             country=self.rwanda,
                                             report_season=self.season,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        # shouldn't have any farmers yet
        recipients = broadcast.get_recipients_for_wetmill(self.nasho)
        self.assertEquals(0, len(recipients))

        # add a farmer for nasho
        farmer = Farmer.objects.create(connection=self.conn1, name="", wetmill=self.nasho)

        # should now have one recipient
        recipients = broadcast.get_recipients_for_wetmill(self.nasho)
        self.assertEquals(1, len(recipients))
        self.assertEquals(farmer, recipients[0])

        # add observers and accountants to this message
        broadcast.recipients = 'AFO'
        broadcast.save()

        # same as before as we don't have an observer or accountants
        recipients = broadcast.get_recipients_for_wetmill(self.nasho)
        self.assertEquals(1, len(recipients))
        self.assertEquals(farmer, recipients[0])

        accountant = Accountant.objects.create(connection=self.conn2, name="", wetmill=self.nasho)
        observer = WetmillObserver.objects.create(connection=self.conn3, name="", wetmill=self.nasho)

        recipients = broadcast.get_recipients_for_wetmill(self.nasho)
        self.assertEquals(3, len(recipients))
        self.assertEquals(accountant, recipients[0])
        self.assertEquals(farmer, recipients[1])
        self.assertEquals(observer, recipients[2])

    def test_sending(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()
        
        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("2"))

        broadcast = Broadcast.objects.create(recipients='F',
                                             text="Hello {{wetmill.name}}",
                                             country=self.rwanda,
                                             report_season=self.season,
                                             created_by=self.admin,
                                             modified_by=self.admin)

        SeasonAggregate.calculate_for_season(self.season)

        # should not have any pending broadcasts
        self.assertFalse(Broadcast.get_pending(datetime.datetime.now()))

        # set a time for five minutes from now
        five_minute_future = datetime.datetime.now() + datetime.timedelta(minutes=5)
        broadcast.send_on = five_minute_future
        broadcast.save()

        # still no broadcasts
        self.assertFalse(Broadcast.get_pending(datetime.datetime.now()))

        # ok, set it to five minutes ago instead
        five_minute_past = datetime.datetime.now() - datetime.timedelta(minutes=5)
        broadcast.send_on = five_minute_past
        broadcast.save()

        # should now get our one broadcast
        pending = Broadcast.get_pending(datetime.datetime.now())
        self.assertTrue(1, len(pending))
        self.assertTrue(broadcast.pk, pending[0].pk)

        # add a farmer for nasho
        farmer = Farmer.objects.create(connection=self.conn1, name="", wetmill=self.nasho)
        
        # and one for coko
        farmer = Farmer.objects.create(connection=self.conn2, name="", wetmill=self.coko)

        # send the broadcast
        broadcast.send()

        # make sure we were sent
        self.assertTrue(broadcast.sent)

        messages = broadcast.messages.all().order_by('text')
        self.assertEquals(2, len(messages))
        self.assertEquals(self.conn2, messages[0].connection)
        self.assertEquals("Hello Coko", messages[0].text)
        self.assertEquals(self.conn1, messages[1].connection)
        self.assertEquals("Hello Nasho", messages[1].text)

        # reset everything
        broadcast.sent = False
        broadcast.messages.all().delete()

        # set a conditional message
        broadcast.text = "{% if wetmill.name == 'Nasho' %}Hi Nasho{% endif %}"
        broadcast.save()

        # send the broadcast
        broadcast.send()

        # make sure we were sent
        self.assertTrue(broadcast.sent)
        messages = broadcast.messages.all()
        self.assertEquals(1, len(messages))
        self.assertEquals(self.conn1, messages[0].connection)
        self.assertEquals("Hi Nasho", messages[0].text)

    def test_views(self):
        self.season = self.rwanda_2010
        self.configure_season()
        self.create_connections()

        # add a nasho accountant
        accountant = Accountant.objects.create(connection=self.conn2, name="Nic", wetmill=self.nasho)        

        response = self.client.get(reverse('broadcasts.broadcast_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        response = self.client.get(reverse('broadcasts.broadcast_list'))
        self.assertEquals(0, len(response.context['object_list']))

        nasho_report = self.generate_report(self.nasho, Decimal("1"))
        coko_report = self.generate_report(self.coko, Decimal("2"))

        # go to our create
        post_data = dict(country=self.rwanda.id)
        response = self.client.post(reverse('broadcasts.broadcast_create'), post_data)

        # fails cuz we didn't specify anybody to send it to
        self.assertEquals(200, response.status_code)

        post_data['to_accountants'] = 'on'
        post_data['to_farmers'] = 'on'
        post_data['to_observers'] = 'on'

        post_data['report_season'] = self.season.id
        post_data['country'] = self.kenya.id

        # fails cuz our report season is different than our country
        response = self.client.post(reverse('broadcasts.broadcast_create'), post_data)
        self.assertEquals(200, response.status_code)

        # fails due to sms season and country mismatch
        post_data['sms_season'] = self.season.id
        del post_data['report_season']
        response = self.client.post(reverse('broadcasts.broadcast_create'), post_data)
        self.assertEquals(200, response.status_code)

        # put it back in an ok state
        post_data['report_season'] = self.season.id
        post_data['country'] = self.rwanda.id
        del post_data['sms_season']

        # this time we will fail because there are no wetmills with finalized reports for this season
        response = self.client.post(reverse('broadcasts.broadcast_create'), post_data)
        self.assertEquals(200, response.status_code)

        # lets finalize the reports
        SeasonAggregate.calculate_for_season(self.season)

        # this one should work
        response = self.client.post(reverse('broadcasts.broadcast_create'), post_data)
        broadcast = Broadcast.objects.get()
        self.assertRedirect(response, reverse('broadcasts.broadcast_message', args=[broadcast.id]))
        
        # get the message page
        response = self.client.get(reverse('broadcasts.broadcast_message', args=[broadcast.id]))

        # set our sms season
        broadcast.sms_season = self.season
        broadcast.save()

        # get our page again
        response = self.client.get(reverse('broadcasts.broadcast_message', args=[broadcast.id]))

        # back to just report
        broadcast.sms_season = None
        broadcast.save()

        # try to do a preview
        import simplejson as json
        response = self.client.get(reverse('broadcasts.broadcast_preview', args=[broadcast.id]) + "?text=hello {{wetmill.name}}&wetmill_id=" + str(self.nasho.id) + "&_format=json")
        json_response = json.loads(response.content)
        self.assertEquals('hello Nasho', json_response['preview'])

        # preview with no text
        response = self.client.get(reverse('broadcasts.broadcast_preview', args=[broadcast.id]) + "?text=+&wetmill_id=" + str(self.nasho.id) + "&_format=json")
        json_response = json.loads(response.content)
        self.assertTrue(json_response['preview'].find('** No text') == 0)

        response = self.client.get(reverse('broadcasts.broadcast_preview', args=[broadcast.id]) + "?text={%if asasdf asdf %}&wetmill_id=" + str(self.nasho.id) + "&_format=json")
        json_response = json.loads(response.content)
        self.assertTrue(json_response['preview'].find('** Error') == 0)

        # ok set our message
        post_data = dict(text="hello {{wetmill.name}}")
        response = self.client.post(reverse('broadcasts.broadcast_message', args=[broadcast.id]), post_data)

        self.assertRedirect(response, reverse('broadcasts.broadcast_test', args=[broadcast.id]))

        post_data = dict(send_date='January 16, 2013', send_time='15:30')
        response = self.client.post(reverse('broadcasts.broadcast_schedule', args=[broadcast.id]), post_data)        

        self.assertRedirect(response, reverse('broadcasts.broadcast_read', args=[broadcast.id]))
        response = self.client.get(reverse('broadcasts.broadcast_read', args=[broadcast.id]))

        response = self.client.get(reverse('broadcasts.broadcast_update', args=[broadcast.id]))
        self.assertEquals(200, response.status_code)

        post_data = dict(country=self.season.country.id, report_season=self.season.id, to_accountants='on', to_farmers='on', to_observers='on')
        response = self.client.post(reverse('broadcasts.broadcast_update', args=[broadcast.id]), post_data)

        response = self.client.get(reverse('broadcasts.broadcast_schedule', args=[broadcast.id]))
        self.assertEquals(200, response.status_code)

        # add a farmer for nasho
        farmer = Farmer.objects.create(connection=self.conn1, name="", wetmill=self.nasho)

        # test our test view
        response = self.client.get(reverse('broadcasts.broadcast_test', args=[broadcast.id]))
        self.assertEquals(200, response.status_code)

        # should have one message for our single farmer
        previews = response.context['test_messages']
        self.assertEquals(1, len(previews))
        self.assertEquals(self.nasho, previews[0]['wetmill'])
        self.assertEquals("hello Nasho", previews[0]['text'])

        # change to an empty message
        broadcast.text = ""
        broadcast.save()

        response = self.client.get(reverse('broadcasts.broadcast_test', args=[broadcast.id]))
        previews = response.context['test_messages']
        self.assertTrue(previews[0]['text'].find("** No text") == 0)

        # error template
        broadcast.text = "{% if asdf asdf %}"
        broadcast.save()

        response = self.client.get(reverse('broadcasts.broadcast_test', args=[broadcast.id]))
        previews = response.context['test_messages']
        self.assertTrue(previews[0]['text'].find("** Error") == 0)

        
        

        

                                             
