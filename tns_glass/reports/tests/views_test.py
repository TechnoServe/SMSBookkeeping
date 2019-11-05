from datetime import datetime
from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from reports.models import Report, Sale, SaleComponent
from grades.models import Grade
from decimal import Decimal
from cashuses.models import CashUse
from cashsources.models import CashSource
from farmerpayments.models import FarmerPayment
from expenses.models import Expense
from .base import PDFTestCase
from seasons.models import SeasonGrade

from guardian.shortcuts import remove_perm, assign

class ReportTestCase(PDFTestCase):

    def test_report_editing(self):
        # not logged in, no dice
        response = self.client.get(reverse('reports.report_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, reverse('users.user_login'))

        # assign view permission the the viewer user
        assign("wetmills.wetmill_report_view", self.viewer)
        self.login(self.viewer)

        response = self.client.get(reverse('reports.report_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, reverse('users.user_login'))        
        self.client.logout()

        # finalize the report
        self.report.delete()
        self.report = Report.objects.create(wetmill=self.nasho, season=self.rwanda_2010, created_by=self.admin, modified_by=self.admin)
        self.report.is_finalized = True
        self.report.save()

        # the login, the viewer will now have a chance to view one report
        self.login(self.viewer)
        response = self.client.get(reverse('reports.report_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, reverse('reports.report_read', args=[self.report.id]))

        # logout
        self.client.logout()
        
        # try to access the report anonymously
        response = self.client.get(reverse('reports.report_read', args=[self.report.id]))
        self.assertRedirect(response, reverse('users.user_login'))

        # delete the report object after use
        self.report.delete()
        
        self.login(self.admin)
        # shouldn't be a report for nasho, 2010 yet
        self.assertEquals(0, Report.objects.filter(wetmill=self.nasho, season=self.rwanda_2010).count())

        # first time doing a lookup, we'll actually create the report
        response = self.client.get(reverse('reports.report_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        report = Report.objects.get(wetmill=self.nasho, season=self.rwanda_2010)
        read_url = reverse('reports.report_read', args=[report.id])
        self.assertRedirect(response, read_url)

        # second time through it already exists, so should return the same report
        response = self.client.get(reverse('reports.report_lookup', args=[self.nasho.id, self.rwanda_2010.id]))
        self.assertRedirect(response, read_url)

        # check the list page, make sure our report exists there
        response = self.client.get(reverse('reports.report_list'))
        self.assertEquals(1, len(response.context['report_list']))
        self.assertContains(response, "Nasho")

    def test_report_attributes(self):
        self.login(self.admin)

        # configure 2010 to contain some uses of cash
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

        bonus = FarmerPayment.objects.create(name="Bonus", order=3, created_by=self.admin, modified_by=self.admin)
        self.rwanda_2010.add_farmer_payment(bonus, 'ALL')

        self.rwanda_2010.add_cash_use(self.cu_second_payment)
        self.rwanda_2010.add_cash_use(self.cu_dividend)

        report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        read_url = reverse('reports.report_read', args=[report.id])

        edit_attributes_url = reverse('reports.report_attributes', args=[report.id])
        response = self.client.get(read_url)
        self.assertContains(response, edit_attributes_url)

        # load our attributes page
        response = self.client.get(edit_attributes_url)

        second_key = 'cashuse__%d' % self.cu_second_payment.id
        dividend_key = 'cashuse__%d' % self.cu_dividend.id
        bonus_key = 'payment__%d__all_kil' % bonus.id
        misc_key = 'cashsource__%d' % self.cs_misc_sources.id

        # make sure those fields are present
        self.assertTrue(second_key in response.context['form'].fields)
        self.assertTrue(dividend_key in response.context['form'].fields)

        post_data = { 'working_capital': "10500", 
                      dividend_key: "20000",
                      bonus_key: "100",
                      misc_key: "100",
                      second_key: "15000"    }
        response = self.assertPost(edit_attributes_url, post_data)

        report = Report.objects.get(pk=report.id)
        self.assertEquals(Decimal("10500"), report.working_capital)
        
        cashuses = report.cash_uses.all()
        self.assertEquals(2, len(cashuses))

        self.assertEquals(self.cu_dividend, cashuses[0].cash_use)
        self.assertEquals(Decimal("20000"), cashuses[0].value)

        self.assertEquals(self.cu_second_payment, cashuses[1].cash_use)
        self.assertEquals(Decimal("15000"), cashuses[1].value)

        # hit our update page, test the initial data
        response = self.client.get(edit_attributes_url)
        self.assertEquals(Decimal("20000"), response.context['form'].initial[dividend_key])        
        self.assertEquals(Decimal("15000"), response.context['form'].initial[second_key])        
        self.assertEquals(Decimal("100"), response.context['form'].initial[bonus_key])        

        # make sure the new values show up on our read page
        response = self.client.get(read_url)

        self.assertContains(response, "Dividend")
        self.assertContains(response, "20,000 RWF")

        self.assertContains(response, "Second Payment")
        self.assertContains(response, "15,000 RWF")

        self.assertContains(response, "Bonus")

    def test_report_production(self):
        self.login(self.admin)
        report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)

        # add two grades to our 2010 season
        self.add_grades()
        self.rwanda_2010.grades.clear()
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.green15)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.parchment)

        green_key = 'production__%d' % self.green.id
        green15_key = 'production__%d' % self.green15.id
        low_key = 'production__%d' % self.low.id
        parchment_key = 'production__%d' % self.parchment.id
        cherry_key = 'production__%d' % self.cherry.id

        production_url = reverse('reports.report_production', args=[report.id])

        response = self.client.get(production_url)
        form = response.context['form']
        self.assertFalse(green_key in form.fields)
        self.assertTrue(green15_key in form.fields)
        self.assertTrue(low_key in form.fields)
        self.assertFalse(cherry_key in form.fields)

        post_data = { green15_key: "16641", low_key: "1856", "capacity": "30000" }
        response = self.assertPost(production_url, post_data)

        report = Report.objects.get(pk=report.pk)
        self.assertEquals(Decimal("30000"), report.capacity)

        production = report.production.all()
        self.assertEquals(2, len(production))
        self.assertEquals(self.green15, production[0].grade)
        self.assertEquals(Decimal("16641"), production[0].volume)
        self.assertEquals(self.low, production[1].grade)
        self.assertEquals(Decimal("1856"), production[1].volume)

        post_data = { green15_key: "16651" }
        response = self.assertPost(production_url, post_data)

        report = Report.objects.get(pk=report.pk)
        self.assertIsNone(report.capacity)

        production = report.production.all()
        self.assertEquals(1, len(production))
        self.assertEquals(self.green15, production[0].grade)
        self.assertEquals(Decimal("16651"), production[0].volume)            

        post_data = { green15_key: "16661", low_key: "0", "capacity": "0" }
        response = self.assertPost(production_url, post_data)
        
        report = Report.objects.get(pk=report.pk)
        self.assertEquals(Decimal("0"), report.capacity)

        production = report.production.all()
        self.assertEquals(2, len(production))
        self.assertEquals(self.green15, production[0].grade)
        self.assertEquals(Decimal("16661"), production[0].volume)
        self.assertEquals(self.low, production[1].grade)
        self.assertEquals(Decimal("0"), production[1].volume)

        response = self.client.get(production_url)
        self.assertInitial(response, green15_key, Decimal("16661"))

        # make sure the values are shown on our read page
        response = self.client.get(reverse('reports.report_read', args=[report.id]))

        self.assertContains(response, "16,661 Kg")
        self.assertContains(response, "Parchment")

    def test_production_for_kind(self):
        report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        self.add_grades()

        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()

        self.rwanda_2010.add_grade(self.cherry)
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.low)

        self.assertIsNone(report.production_for_kind('GRE'))
        report.production.create(grade=self.low, volume=Decimal("1000"),
                                 created_by=self.admin, modified_by=self.admin)

        self.assertEquals(Decimal("1000"), report.production_for_kind('GRE'))

        report.production.create(grade=self.green, volume=Decimal("2000"),
                                 created_by=self.admin, modified_by=self.admin)

        self.assertEquals(Decimal("3000"), report.production_for_kind('GRE'))

        season_production = report.production_for_season_grades()
        self.assertEquals(3, len(season_production))

        self.assertEquals(self.cherry, season_production[0]['grade'])
        self.assertIsNone(season_production[0]['volume'])

        self.assertEquals(self.green, season_production[1]['grade'])
        self.assertEquals(Decimal("2000"), season_production[1]['volume'])

        season_production = report.production_for_season_grades('GRE')
        self.assertEquals(2, len(season_production))
        
        self.assertEquals(self.green, season_production[0]['grade'])
        self.assertEquals(Decimal("2000"), season_production[0]['volume'])

        self.assertEquals(self.low, season_production[1]['grade'])
        self.assertEquals(Decimal("1000"), season_production[1]['volume'])

    def test_cherry_production_by_non_members(self):
        report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)

        self.add_grades()
        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()
        self.rwanda_2010.add_grade(self.cherry)

        # no cherry production set, so None
        self.assertIsNone(report.cherry_production_by_non_members())

        # add cherry production
        report.production.create(grade=self.cherry, volume=Decimal("30000"),
                                 created_by=self.admin, modified_by=self.admin)

        # no value, since we don't know member production
        self.assertIsNone(report.cherry_production_by_non_members())        

        # clear out productions
        report.production.all().delete()

        # if we set the member cherry production, same thing, we don't know total
        report.cherry_production_by_members = Decimal("10000")
        report.save()

        self.assertIsNone(report.cherry_production_by_non_members())

        # now both the cherry production and the member value is set, we can calcualte the value
        report.production.create(grade=self.cherry, volume=Decimal("30000"),
                                 created_by=self.admin, modified_by=self.admin)

        self.assertEquals(Decimal("20000"), report.cherry_production_by_non_members())

    def setupExpenses(self):
        self.report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        super(PDFTestCase, self).add_expenses()

        self.rwanda_2010.add_expense(self.expense_washing_station)
        self.rwanda_2010.add_expense(self.expense_other)
        self.rwanda_2010.add_expense(self.expense_taxes)
        self.rwanda_2010.add_expense(self.expense_cherry_advance)
        self.rwanda_2010.add_expense(self.expense_capex)
        self.rwanda_2010.add_expense(self.expense_capex_interest)

    def test_season_expense_entries(self):
        self.setupExpenses()

        entries = self.report.entries_for_season_expenses()
        self.assertEquals(6, len(entries))
        self.assertEquals(self.expense_washing_station, entries[0]['expense'])
        self.assertEquals(0, entries[0]['expense'].depth)
        self.assertEquals(None, entries[0]['value'])
        self.assertEquals(None, entries[0]['exchange_rate'])

        self.assertEquals(self.expense_cherry_advance, entries[1]['expense'])
        self.assertEquals(1, entries[1]['expense'].depth)

        self.assertEquals(self.expense_other, entries[2]['expense'])
        self.assertEquals(1, entries[2]['expense'].depth)

        self.assertEquals(self.expense_taxes, entries[3]['expense'])
        self.assertEquals(2, entries[3]['expense'].depth)

        self.assertEquals(self.expense_capex, entries[4]['expense'])
        self.assertEquals(0, entries[4]['expense'].depth)

        self.assertEquals(self.expense_capex_interest, entries[5]['expense'])
        self.assertEquals(1, entries[5]['expense'].depth)

        self.report.expenses.create(expense=self.expense_cherry_advance, value=Decimal("10000"),
                                    created_by=self.admin, modified_by=self.admin)

        entries = self.report.entries_for_season_expenses()        
        self.assertEquals(6, len(entries))
        self.assertEquals(self.expense_cherry_advance, entries[1]['expense'])        
        self.assertEquals(Decimal("10000"), entries[1]['value'])

    def test_expense_entry(self):
        self.setupExpenses()

        self.report.expenses.create(expense=self.expense_cherry_advance, value=Decimal("10000"),
                                    created_by=self.admin, modified_by=self.admin)

        self.report.expenses.create(expense=self.expense_capex_interest, value=Decimal("100"),
                                    exchange_rate=Decimal("565"), created_by=self.admin, modified_by=self.admin)

        # test that expenses show up on the read page
        self.login(self.admin)
        response = self.client.get(reverse('reports.report_read', args=[self.report.id]))
        self.assertContains(response, "10,000 RWF")
        self.assertContains(response, "Other Expenses")
        self.assertContains(response, "$100.00")

    def test_pdf_report(self):
        self.setupExpenses()

        # try to get a pdf report, remember this user haven't any permission
        self.login(self.viewer)
        response = self.client.get(reverse('reports.report_pdf', args=[self.report.id]))
        # should be redirected, you don't have permission fella..
        self.assertEquals(302, response.status_code)
        self.client.logout()

        # lets upgrade this user to be a viewer
        assign('wetmills.wetmill_report_view', self.viewer)
        self.login(self.viewer)
        response = self.client.get(reverse('reports.report_pdf', args=[self.report.id]))
        # it works!
        self.assertEquals(200, response.status_code)
        self.client.logout()

        # try again with a strong dude! Admin...
        self.login(self.admin)
        response = self.client.get(reverse('reports.report_pdf', args=[self.report.id]))
        # everybody! open the doors and pay respect to the admin
        self.assertEquals(200, response.status_code)

    def test_local_sales(self):
        self.report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        self.login(self.admin)

        self.add_grades()
        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.parchment)

        create_url = reverse('reports.sale_create') + "?report=%d" % self.report.id
        response = self.client.get(create_url)

        # there shouldn't be local sales present, rwanda 2010 doesn't support them
        self.assertEquals(2, len(response.context['form'].fields['sale_type'].choices))

        # but if we change the season to support them, then it should show
        self.rwanda_2010.has_local_sales = True
        self.rwanda_2010.save()
        
        create_url = reverse('reports.sale_create') + "?report=%d" % self.report.id
        response = self.client.get(create_url)
        self.assertEquals(3, len(response.context['form'].fields['sale_type'].choices))

        # create one of the sales
        post_data = { 'buyer': "Rwanda Trading Company",
                      'date': "October 20, 2011",
                      'price': "300000",
                      'currency': self.rwf.id,
                      'sale_type': 'LOC',
                      'adjustment': "0.65" } # this adjustment should be cleared

        # try to post again with an invalid volume
        post_data['component_grade__0'] =  self.green.id
        post_data['component_volume__0'] = "10000"
        post_data['component_count'] = 1

        response = self.assertPost(create_url, post_data)

        sales = self.report.sales.all()
        self.assertEquals(1, len(sales))

        sale = sales[0]
        self.assertEquals("Rwanda Trading Company", sale.buyer)
        self.assertEquals('LOC', sale.sale_type)
        self.assertIsNone(sale.adjustment)
        self.assertEquals(1, sale.components.count())
        self.assertEquals(Decimal("10000"), sale.components.all()[0].volume)
        self.assertEquals(self.green, sale.components.all()[0].grade)

    def test_sale_entry(self):
        self.report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        self.login(self.admin)

        self.add_grades()
        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.parchment)

        create_url = reverse('reports.sale_create') + "?report=%d" % self.report.id
        response = self.client.get(create_url)

        self.assertContains(response, "Parchment")
        self.assertNotContains(response, "Cherry")

        self.assertContains(response, "Rwandan Francs")
        self.assertNotContains(response, "Kenyan Shillings")

        # make sure it contains the default exchange rate for the season too
        self.assertContains(response, "%f" % self.report.season.exchange_rate)

        post_data = { 'buyer': "Rwanda Trading Company",
                      'date': "October 20, 2011",
                      'price': "300000",
                      'currency': self.rwf.id,
                      'sale_type': 'FOT',
                      'adjustment': "0.65" }

        # we should fail on creating this sale because at least one component hasn't been added to the sale
        response = self.client.post(create_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)
        self.assertEquals(1, len(response.context['form'].errors))

        # try to post again with an invalid volume
        post_data['component_grade__0'] =  self.green.id
        post_data['component_volume__0'] = "asdf"
        post_data['component_count'] = 1

        # should fail again, volume isn't a number
        response = self.client.post(create_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)
        self.assertEquals(2, len(response.context['form'].errors))
        self.assertEquals(1, response.context['component_count'])

        post_data['component_grade__0'] =  self.green.id
        post_data['component_volume__0'] = "1000"

        post_data['component_grade__1'] =  self.low.id
        post_data['component_volume__1'] = "100"

        # now try posting in USD's but with no exchange rate
        post_data['currency'] = self.usd.id
        response = self.client.post(create_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)
        self.assertEquals(1, len(response.context['form'].errors))

        # ok, fill out the exchange rate
        post_data['exchange_rate'] = "565"
        response = self.assertPost(create_url, post_data)

        sales = self.report.sales.all()
        self.assertEquals(1, len(sales))

        sale = sales[0]
        self.assertEquals("Rwanda Trading Company", sale.buyer)
        self.assertEquals(2, sale.components.count())
        self.assertEquals(Decimal("1000"), sale.components.all()[0].volume)
        self.assertEquals(self.green, sale.components.all()[0].grade)
        self.assertEquals(Decimal("100"), sale.components.all()[1].volume)
        self.assertEquals(self.low, sale.components.all()[1].grade)

        self.assertEquals(Decimal("1100"), sale.total_volume())
        self.assertEquals("Green, Low Grades", sale.all_grades())

        update_url = reverse('reports.sale_update', args=[sale.id])
        response = self.client.get(update_url)

        self.assertInitial(response, 'buyer', 'Rwanda Trading Company')
        self.assertInitial(response, 'price', Decimal('300000'))
        self.assertInitial(response, 'sale_type', 'FOT')

        self.assertInitial(response, 'component_grade__0', self.green)
        self.assertInitial(response, 'component_volume__0', Decimal("1000"))

        self.assertInitial(response, 'component_grade__1', self.low)
        self.assertInitial(response, 'component_volume__1', Decimal("100"))

        self.assertEquals(2, response.context['component_count'])

        del post_data['component_grade__0']
        del post_data['component_volume__0']
        post_data['buyer'] = "RTC"

        response = self.assertPost(update_url, post_data)

        sale = Sale.objects.get(pk=sale.pk)
        self.assertEquals("RTC", sale.buyer)
        self.assertEquals(1, sale.components.count())
        self.assertEquals(Decimal("100"), sale.components.all()[0].volume)
        self.assertEquals(self.low, sale.components.all()[0].grade)

        delete_url = reverse('reports.sale_delete', args=[sale.id])
        response = self.client.get(delete_url)
        self.assertEquals(200, response.status_code)
        self.assertContains(response, sale.buyer)

        response = self.assertPost(delete_url, dict())
        self.assertAtURL(response, reverse('reports.report_read', args=[self.report.id]))

        # all sales removed for this report
        self.assertEquals(0, self.report.sales.count())

    def test_expense_form(self):
        self.setupExpenses()
        self.login(self.admin)

        washing_key = 'expense__%d' % self.expense_washing_station.id
        other_key = 'expense__%d' % self.expense_other.id
        taxes_key = 'expense__%d' % self.expense_taxes.id
        cherry_key = 'expense__%d' % self.expense_cherry_advance.id
        unexplained_key = 'expense__%d' % self.expense_unexplained.id

        interest_key = 'expense__%d' % self.expense_capex_interest.id
        interest_exchange_key = 'expense__exchange__%d' % self.expense_capex_interest.id

        expense_url = reverse('reports.report_expenses', args=[self.report.id])
        response = self.client.get(expense_url)

        form = response.context['form']
        self.assertTrue(taxes_key in form.fields)
        self.assertTrue(cherry_key in form.fields)
        self.assertTrue(interest_key in form.fields)
        self.assertTrue(interest_exchange_key in form.fields)
        self.assertFalse(washing_key in form.fields)
        self.assertFalse(other_key in form.fields)
        self.assertFalse(unexplained_key in form.fields)

        post_data = { taxes_key: "0",
                      cherry_key: "10000",
                      interest_key: "100",
                      interest_exchange_key: "565" }

        response = self.assertPost(expense_url, post_data)

        entries = self.report.expenses.all()
        self.assertEquals(3, len(entries))
        self.assertEquals(self.expense_capex_interest, entries[0].expense)
        self.assertEquals(Decimal("100"), entries[0].value)
        self.assertEquals(Decimal("565"), entries[0].exchange_rate)
        self.assertEquals(self.expense_cherry_advance, entries[1].expense)
        self.assertEquals(Decimal("10000"), entries[1].value)
        self.assertEquals(None, entries[1].exchange_rate)
        self.assertEquals(self.expense_taxes, entries[2].expense)
        self.assertEquals(Decimal("0"), entries[2].value)
        self.assertEquals(None, entries[2].exchange_rate)

        response = self.client.get(expense_url)

        # check initial values of the form
        self.assertInitial(response, taxes_key, Decimal("0"))
        self.assertInitial(response, cherry_key, Decimal("10000"))
        self.assertInitial(response, interest_key, Decimal("100"))
        self.assertInitial(response, interest_exchange_key, Decimal("565"))
        
        post_data = { taxes_key: "0" }
        response = self.assertPost(expense_url, post_data)

        entries = self.report.expenses.all()
        self.assertEquals(1, len(entries))
        self.assertIn("Taxes - 0", str(entries[0]))
        self.assertEquals(self.expense_taxes, entries[0].expense)
        self.assertEquals(Decimal("0"), entries[0].value)

    def test_report_finalize(self):
        self.setupExpenses()

        # add a calculated expense
        freight_and_insurance = Expense.objects.create(name="Freight and Insurance", parent=None, order=10,
                                                       calculated_from='FREIGHT', created_by=self.admin, modified_by=self.admin)
        self.rwanda_2010.add_expense(freight_and_insurance)

        self.add_grades()
        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.green15)
        self.rwanda_2010.add_grade(self.green13)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.ungraded)
        self.rwanda_2010.add_grade(self.parchment)
        self.rwanda_2010.add_grade(self.cherry)

        self.add_cash_uses()
        self.rwanda_2010.cash_uses.clear()
        self.rwanda_2010.add_cash_use(self.cu_dividend)
        self.report.cash_uses.all().delete()

        self.add_cash_sources()
        self.rwanda_2010.cash_sources.clear()
        self.rwanda_2010.add_cash_source(self.cs_misc_sources)
        self.rwanda_2010.add_cash_source(self.cs_unused_working_cap)
        self.report.cash_sources.all().delete()

        self.add_farmer_payments()
        self.rwanda_2010.farmer_payments.all().delete()
        bonus = FarmerPayment.objects.create(name="Bonus", order=3, created_by=self.admin, modified_by=self.admin)
        agents = FarmerPayment.objects.create(name="Agents", order=4, created_by=self.admin, modified_by=self.admin)
        self.rwanda_2010.add_farmer_payment(self.fp_dividend, 'MEM')
        self.rwanda_2010.add_farmer_payment(self.fp_second_payment, 'BOT')
        self.rwanda_2010.add_farmer_payment(bonus, 'NON')
        self.rwanda_2010.add_farmer_payment(agents, 'ALL')
        self.report.farmer_payments.all().delete()

        self.report.capacity = None
        self.report.farmers = None
        self.report.save()

        self.login(self.admin)

        read_url = reverse('reports.report_read', args=[self.report.id])
        finalize_url = reverse('reports.report_finalize', args=[self.report.id])

        post_data = dict()

        # finalize the report without any entry
        response = self.assertPost(finalize_url, post_data)

        messages = [message for message in response.context['messages']]

        # verify if redirected to report read page
        self.assertAtURL(response, read_url)

        # verify if there are any message
        self.assertGreater(len(messages), 0)

        # look if the message is an error
        self.assertEqual(40, messages[0].level)

        # check for generic message
        self.assertIn('Unable to finalize report due to missing field values. Please fill out these fields and try again:', messages[0].message)

        self.report.capacity = Decimal("10000")
        self.report.farmers = 100
        self.report.save()

        # check atleast one production
        self.assertIn('15+', messages[0].message)

        # check atleast one expense
        self.assertIn('Cherry Advance', messages[0].message)

        # check if all supposed cashuses
        self.assertIn('Bonus', messages[0].message)
        self.assertIn('Agents', messages[0].message)

        # add production data entries and finalize, should require for all data entries
        self.report.capacity = 30000
        self.report.cherry_production_by_members = 28249

        self.report.production.create(grade=self.green15, volume=12344, created_by=self.admin,
                                      modified_by=self.admin)
        self.report.production.create(grade=self.green13, volume=648, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.low, volume=839, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.ungraded, volume=123, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.parchment, volume=4873, created_by=self.admin,
                                      modified_by=self.admin)
        self.report.production.create(grade=self.cherry, volume=61128, created_by=self.admin, modified_by=self.admin)

        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, 
                                           member_per_kilo=Decimal("1234"),
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=self.fp_second_payment, 
                                           member_per_kilo=Decimal("1234"), non_member_per_kilo=Decimal("1234"),
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=bonus, 
                                           non_member_per_kilo=Decimal("1234"), 
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=agents, 
                                           all_per_kilo=Decimal("1234"), 
                                           created_by=self.admin, modified_by=self.admin)

        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("1234"),
                                     created_by=self.admin, modified_by=self.admin)
        self.report.cash_sources.create(cash_source=self.cs_misc_sources, value=Decimal("1234"),
                                        created_by=self.admin, modified_by=self.admin)

        response = self.assertPost(finalize_url, post_data)

        messages = [message for message in response.context['messages']]      

        # verify if redirected to report read page
        self.assertAtURL(response, read_url)

        # look if the message is an error
        self.assertEqual(40, messages[0].level)

        # check if the grade 15+ is no more in empty fields
        self.assertNotIn('15+', messages[0].message)

        # expenses should be there.
        self.assertIn('Cherry Advance', messages[0].message)

        # fill all remaining entries except sales
        self.report.working_capital = 9000000
        self.report.miscellaneous_sources = 0
        self.report.dividend_to_members = 0
        
        self.report.save()

        self.report.expenses.create(report=self.report, expense=self.expense_cherry_advance, value=100, 
                                    exchange_rate="500", created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_taxes, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_unexplained, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_capex_interest, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)

        response = self.assertPost(finalize_url, post_data)

        messages = [message for message in response.context['messages']]        

        # verify if redirected to report read page
        self.assertAtURL(response, read_url)

        # look if the message is still an error message
        self.assertEqual(40, messages[0].level)

        # expenses shouldn't be there anymore
        self.assertNotIn('Cherry Advance', messages[0].message)

        # the only remaining is sale as expected
        self.assertIn('Add at least one sale', messages[0].message)
        
        # add sales on the report
        kigali_coffee = Sale.objects.create(report=self.report, date=datetime.today(), buyer="Kigali Coffee", currency=self.rwf,
                                            price=100, sale_type="FOT", adjustment='0.16',
                                            created_by=self.admin, modified_by=self.admin)
        kigali_coffee_comp = SaleComponent.objects.create(sale=kigali_coffee, grade=self.green15, volume=10, created_by=self.admin,
                                                          modified_by=self.admin)

        # finalize the report for, and boom voila! Working...
        response = self.assertPost(finalize_url, post_data)

        messages = [message for message in response.context['messages']]        

        # verify if redirected to report read page
        self.assertAtURL(response, read_url)
        
        # look if the message is a success
        self.assertEqual(25, messages[0].level)

        # check if the report finalized flag has been set to true
        report = Report.objects.get(pk=self.report.pk)
        self.assertTrue(report.is_finalized)

        # check for other report data
        self.assertEquals(Decimal('9000000'), report.working_capital)

        # list our reports
        response = self.client.get(reverse('reports.report_list'))

        # make sure our report is displayed as finalized
        self.assertContains(response, "Yes")

        # see if the report comes back as a finalized report, shouldn't since the season
        # is not finalized yet
        self.assertIsNone(report.wetmill.get_most_recent_transparency_report())

        # but if we finalize the season
        season = report.season
        season.is_finalized = True
        season.save()
        
        self.assertEquals(report, report.wetmill.get_most_recent_transparency_report())

    def test_report_amending(self):
        self.setupExpenses()

        # add a calculated expense
        freight_and_insurance = Expense.objects.create(name="Freight and Insurance", parent=None, order=10,
                                                       calculated_from='FREIGHT', created_by=self.admin, modified_by=self.admin)
        self.rwanda_2010.add_expense(freight_and_insurance)

        self.add_grades()
        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.green15)
        self.rwanda_2010.add_grade(self.green13)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.ungraded)
        self.rwanda_2010.add_grade(self.parchment)
        self.rwanda_2010.add_grade(self.cherry)

        self.add_cash_uses()
        self.rwanda_2010.cash_uses.clear()
        self.rwanda_2010.add_cash_use(self.cu_dividend)
        self.report.cash_uses.all().delete()

        self.add_cash_sources()
        self.rwanda_2010.cash_sources.clear()
        self.rwanda_2010.add_cash_source(self.cs_misc_sources)
        self.rwanda_2010.add_cash_source(self.cs_unused_working_cap)
        self.report.cash_sources.all().delete()

        self.add_farmer_payments()
        self.rwanda_2010.farmer_payments.all().delete()
        bonus = FarmerPayment.objects.create(name="Bonus", order=3, created_by=self.admin, modified_by=self.admin)
        agents = FarmerPayment.objects.create(name="Agents", order=4, created_by=self.admin, modified_by=self.admin)
        self.rwanda_2010.add_farmer_payment(self.fp_dividend, 'MEM')
        self.rwanda_2010.add_farmer_payment(self.fp_second_payment, 'BOT')
        self.rwanda_2010.add_farmer_payment(bonus, 'NON')
        self.rwanda_2010.add_farmer_payment(agents, 'ALL')
        self.report.farmer_payments.all().delete()

        # add production data entries and finalize, should require for all data entries
        self.report.capacity = 30000
        self.report.cherry_production_by_members = 28249

        self.report.production.create(grade=self.green15, volume=12344, created_by=self.admin,
                                      modified_by=self.admin)
        self.report.production.create(grade=self.green13, volume=648, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.low, volume=839, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.ungraded, volume=123, created_by=self.admin, modified_by=self.admin)
        self.report.production.create(grade=self.parchment, volume=4873, created_by=self.admin,
                                      modified_by=self.admin)
        self.report.production.create(grade=self.cherry, volume=61128, created_by=self.admin, modified_by=self.admin)

        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, 
                                           member_per_kilo=Decimal("1234"),
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=self.fp_second_payment, 
                                           member_per_kilo=Decimal("1234"), non_member_per_kilo=Decimal("1234"),
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=bonus, 
                                           non_member_per_kilo=Decimal("1234"), 
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=agents, 
                                           all_per_kilo=Decimal("1234"), 
                                           created_by=self.admin, modified_by=self.admin)

        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("1234"),
                                     created_by=self.admin, modified_by=self.admin)
        self.report.cash_sources.create(cash_source=self.cs_misc_sources, value=Decimal("1234"),
                                        created_by=self.admin, modified_by=self.admin)

        # fill all remaining entries
        self.report.working_capital = 9000000
        self.report.miscellaneous_sources = 0
        self.report.dividend_to_members = 0

        self.report.save()

        self.report.expenses.create(report=self.report, expense=self.expense_cherry_advance, value=100, 
                                    exchange_rate="500", created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_taxes, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_unexplained, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)
        self.report.expenses.create(report=self.report, expense=self.expense_capex_interest, value=100, exchange_rate="500",
                                    created_by=self.admin, modified_by=self.admin)

        # add sales on the report
        kigali_coffee = Sale.objects.create(report=self.report, date=datetime.today(), buyer="Kigali Coffee", currency=self.rwf, price=100, sale_type="FOT", adjustment='0.16',
                                           created_by=self.admin, modified_by=self.admin)
        kigali_coffee_comp = SaleComponent.objects.create(sale=kigali_coffee, grade=self.green15, volume=10, created_by=self.admin, modified_by=self.admin)

        # finalize the report
        self.report.is_finalized = True
        self.report.save()

        
        # test sales amendments
        sale_create_url = reverse('reports.sale_create') + '?report=%d' % self.report.id
        sale_update_url = reverse('reports.sale_update', args=[kigali_coffee.id])
        sale_delete_url = reverse('reports.sale_delete', args=[kigali_coffee.id])

        # remove the sole sale
        self.login(self.admin)
        response = self.client.get(sale_update_url)

        # has_more_sale left is a label to allowing the removal while true
        # so can I remove this sale. guess no!
        self.assertFalse(response.context['has_more_sale_left'])

        # add a new sale
        sale_two = Sale.objects.create(report=self.report, date=datetime.today(), buyer="Sale Two", currency=self.rwf, price=100, sale_type="FOT", adjustment='0.16',
                                       created_by=self.admin, modified_by=self.admin)
        kigali_coffee_comp = SaleComponent.objects.create(sale=sale_two, grade=self.green15, volume=10, created_by=self.admin, modified_by=self.admin)
        
        # can I delete a sale now?
        response = self.client.get(sale_update_url)

        # yes we can! ( The Hussein Obama way )
        self.assertTrue(response.context['has_more_sale_left'])

        # now remove a sale from this report
        response = self.assertPost(sale_delete_url, dict())

        # did it work? WORKED!
        self.assertEquals(len(self.report.sales.all()), 1)
        
        # how about the amendment
        self.assertEquals(len(response.context['amendments']), 1)

        post_data = { 'buyer': "Rwanda Trading Company",
                      'date': "October 20, 2011",
                      'price': "300000",
                      'currency': self.rwf.id,
                      'sale_type': 'FOT',
                      'adjustment': "0.65" }

        post_data['component_grade__0'] =  self.green.id
        post_data['component_volume__0'] = "asdf"
        post_data['component_count'] = 1
        
        post_data['component_grade__0'] =  self.green.id
        post_data['component_volume__0'] = "1000"
         
        post_data['component_grade__1'] =  self.low.id
        post_data['component_volume__1'] = "100"
        
        post_data['currency'] = self.usd.id
        post_data['exchange_rate'] = "565"

        # create another sale from the form
        response = self.assertPost(sale_create_url, post_data)

        # now the report's amendments sould increase by one
        self.assertEquals(len(response.context['amendments']), 2)        

        # amend this recently add sale
        post_data['currency'] = self.rwf.id
        sale_update_url = reverse('reports.sale_update', args=[self.report.sales.all()[1].id])
        response = self.assertPost(sale_update_url, post_data)

        post_data['price'] = 32048
        sale_update_url = reverse('reports.sale_update', args=[self.report.sales.all()[1].id])
        response = self.assertPost(sale_update_url, post_data)

        # now the report's amendments sould increase by one
        self.assertEquals(len(response.context['amendments']), 5)

        # test production amendments
        production_amend_url = reverse('reports.report_production', args=[self.report.id])

        post_data = dict()

        post_data['miscelaneous_sources'] = '0'
        post_data['working_capital'] = '90000000'
        post_data['cherry_production_by_members'] = '12354'

        post_data['production__%d' % self.green15.id] = '12354'
        post_data['production__%d' % self.green13.id] = '12354'
        post_data['production__%d' % self.parchment.id] = '12354'
        post_data['production__%d' % self.cherry.id] = '12354'
        post_data['production__%d' % self.ungraded.id] = '12354'

        # amend production with one field missing
        response = self.client.post(production_amend_url, post_data)

        # you cannot amend with empty field
        self.assertAtURL(response, production_amend_url)
        self.assertIn('Unable to amend transparency report because the following fields are missing: Farmers, Capacity', response.content)

        # change the production value to another value
        post_data['capacity'] = '100000'
        post_data['farmers'] = '100'
        response = self.assertPost(production_amend_url, post_data)

        # now a new amendment object has been created.
        self.assertEquals(len(response.context['amendments']), 6)

        # test attributes amendments
        attributes_amend_url = reverse('reports.report_attributes', args=[self.report.id])

        post_data = dict()
        post_data['miscellaneous_sources'] = '0'
        post_data['cashuse__%d' % self.cu_dividend.id] = '1235'
        post_data['cashsource__%d' % self.cs_misc_sources.id] = '1235'
        post_data['capacity'] = '100000'
        post_data['cherry_production_by_members'] = '100000'
        post_data['payment__%d__mem_kil' % self.fp_dividend.id] = '100000'
        post_data['payment__%d__mem_kil' % self.fp_second_payment.id] = '100000'
        post_data['payment__%d__non_kil' % self.fp_second_payment.id] = '100000'
        post_data['payment__%d__non_kil' % bonus.id] = '100000'
        post_data['payment__%d__all_kil' % agents.id] = '100000'

        # save the attributes with one empty field
        response = self.client.post(attributes_amend_url, post_data)        

        # nop! you cannot
        self.assertAtURL(response, attributes_amend_url)
        self.assertIn('Unable to amend transparency report because the following fields are missing: Working capital', response.content)

        # change the attribute value to another value
        post_data['working_capital'] = '100000'
        response = self.assertPost(attributes_amend_url, post_data)        

        # now a new amendment get created
        self.assertEquals(len(response.context['amendments']), 7)

        
        # test expenses amendments
        expenses_amend_url = reverse('reports.report_expenses', args=[self.report.id])

        post_data = dict()

        post_data['expense__%d' % self.expense_cherry_advance.id] = 100
        post_data['expense__%d' % self.expense_capex_interest.id] = 100
        post_data['expense__%d' % self.expense_taxes.id] = 100

        post_data['capacity'] = 0
        post_data['working_capital'] = 0
        post_data['cherry_production_by_members'] = 0

        # save the expenses with empty fields
        response = self.client.post(expenses_amend_url, post_data, follow=True)

        # nop! you cannot
        self.assertAtURL(response, expenses_amend_url)
        self.assertIn('Unable to amend transparency report because the following fields are missing: Capex Interest', response.content)

        # change the expense value to another value
        post_data['miscellaneous_sources'] = 0
        post_data['expense__%d' % self.expense_capex_interest.id] = 100
        post_data['expense__exchange__%d' % self.expense_capex_interest.id] = 100
        response = self.assertPost(expenses_amend_url, post_data)        

        # now a new amendment get created
        self.assertEquals(len(response.context['amendments']), 8)

ReportTestCase.active = True
