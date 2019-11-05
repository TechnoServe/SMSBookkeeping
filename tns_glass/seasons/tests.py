from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *
from decimal import Decimal

class SeasonTestCase(TNSTestCase):

    def setUp(self):
        super(SeasonTestCase, self).setUp()
        self.add_expenses()
        self.add_grades()
        self.add_standards()
        self.add_cash_uses()
        self.add_cash_sources()
        self.add_farmer_payments()

    def add_test_seasons(self):
        self.rwanda_08 = Season.objects.create(name='2008', country=self.rwanda, 
                                               exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                               farmer_income_baseline=Decimal("100"),
                                               fob_price_baseline=Decimal("1.15"),                                               
                                               created_by=self.admin, modified_by=self.admin)
        self.kenya_12 = Season.objects.create(name='2012', country=self.kenya, 
                                              exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                              farmer_income_baseline=Decimal("100"),
                                              fob_price_baseline=Decimal("1.15"),                                               
                                              created_by=self.admin, modified_by=self.admin)
        self.rwanda_13 = Season.objects.create(name='2013', country=self.rwanda, 
                                               exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                               farmer_income_baseline=Decimal("100"),
                                               fob_price_baseline=Decimal("1.15"),                                               
                                               created_by=self.admin, modified_by=self.admin)
        self.kenya_10 = Season.objects.create(name='2010', country=self.kenya, 
                                              exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                              farmer_income_baseline=Decimal("100"),
                                              fob_price_baseline=Decimal("1.15"),                                               
                                              created_by=self.admin, modified_by=self.admin)

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('seasons.season_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        Season.objects.all().delete()

        post_data = dict(name="2020",
                         has_local_sales=0,
                         exchange_rate="585",
                         default_adjustment="0.16",
                         farmer_income_baseline="100", 
                         fob_price_baseline="1.15",
                         country=self.rwanda.id)

        response = self.client.post(reverse('seasons.season_create'), post_data)
        season = Season.objects.get(name="2020")
        self.assertRedirect(response, reverse('seasons.season_update', args=[season.id]))

        post_data['name'] = "2011"

        update_data = dict(farmer_payment_left="0", farmer_payment_right="0",
                           cherry_ratio_left="0", cherry_ratio_right="0",
                           total_costs_left="0", total_costs_right="0",
                           sale_price_left="0", sale_price_right="0")
        post_data.update(update_data)

        response = self.assertPost(reverse('seasons.season_update', args=[season.id]), post_data)
        season = Season.objects.get(pk=season.pk)
        self.assertEqual("2011", season.name)

        self.add_test_seasons()

        response = self.client.get(reverse('seasons.season_list'))
        seasons = response.context['season_list']
        self.assertEquals(self.kenya_12, seasons[0])
        self.assertEquals(self.kenya_10, seasons[1])
        self.assertEquals(self.rwanda_13, seasons[2])
        self.assertEquals(season, seasons[3])
        self.assertEquals(self.rwanda_08, seasons[4])

    def test_ordering(self):
        Season.objects.all().delete()
        self.add_test_seasons()

        # default ordering should be by country name then most recent seasons first
        seasons = Season.objects.all()
        self.assertEquals(self.kenya_12, seasons[0])
        self.assertEquals(self.kenya_10, seasons[1])
        self.assertEquals(self.rwanda_13, seasons[2])
        self.assertEquals(self.rwanda_08, seasons[3])

    def test_season_expenses(self):
        self.login(self.admin)
        Season.objects.all().delete()
        rw2010 = Season.objects.create(name="2010", country=self.rwanda, 
                                       exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                       farmer_income_baseline=Decimal("100"), fob_price_baseline=Decimal("1.15"),                                               
                                       created_by=self.admin, modified_by=self.admin)

        update_url = reverse('seasons.season_update', args=[rw2010.id])
        response = self.client.get(update_url)

        washing_key = 'expense__%d' % self.expense_washing_station.id
        washing_key_collapse = 'expense__%d__collapse' % self.expense_washing_station.id
        cherry_key = 'expense__%d' % self.expense_cherry_advance.id
        cherry_key_collapse = 'expense__%d__collapse' % self.expense_cherry_advance.id        
        other_key = 'expense__%d' % self.expense_other.id
        taxes_key = 'expense__%d' % self.expense_taxes.id

        form_fields = response.context['form'].fields
        self.assertTrue(washing_key in form_fields)

        # should be a collapse field since washing station expenses has children
        self.assertTrue(washing_key_collapse in form_fields)
        self.assertTrue(cherry_key in form_fields)

        # shouldn't be a collapse key, we don't have children
        self.assertFalse(cherry_key_collapse in form_fields)
        self.assertTrue(other_key in form_fields)
        self.assertTrue(taxes_key in form_fields)

        post_data = dict(name="2010", country=self.rwanda.id, exchange_rate="585", default_adjustment="0.16",
                         farmer_income_baseline="100", fob_price_baseline="1.15",
                         farmer_payment_left="0", farmer_payment_right="0",
                         cherry_ratio_left="0", cherry_ratio_right="0",
                         total_costs_left="0", total_costs_right="0",
                         sale_price_left="0", sale_price_right="0")

        post_data[taxes_key] = 1
        post_data[cherry_key] = 1

        self.assertPost(update_url, post_data)

        season_expenses = rw2010.get_expense_tree()
        self.assertEquals(4, len(season_expenses))
        self.assertEquals(self.expense_washing_station, season_expenses[0])
        self.assertTrue(season_expenses[0].is_parent)
        self.assertEquals(self.expense_cherry_advance, season_expenses[1])
        self.assertFalse(season_expenses[1].is_parent)
        self.assertEquals(self.expense_other, season_expenses[2])
        self.assertTrue(season_expenses[2].is_parent)
        self.assertEquals(self.expense_taxes, season_expenses[3])
        self.assertFalse(season_expenses[3].is_parent)

        response = self.client.get(update_url)
        self.assertTrue(response.context['form'].initial[taxes_key])

        del post_data[taxes_key]
        self.assertPost(update_url, post_data)

        season_expenses = rw2010.expenses.all()
        self.assertEquals(2, len(season_expenses))
        self.assertTrue(self.expense_washing_station in  season_expenses)
        self.assertTrue(self.expense_cherry_advance in season_expenses)

        post_data = dict(name="2010", country=self.rwanda.id, exchange_rate="585", default_adjustment="0.16", 
                         farmer_income_baseline="100", fob_price_baseline="1.15",
                         farmer_payment_left="0", farmer_payment_right="0",
                         cherry_ratio_left="0", cherry_ratio_right="0",
                         total_costs_left="0", total_costs_right="0",
                         sale_price_left="0", sale_price_right="0")

        post_data[washing_key] = 1
        post_data[washing_key_collapse] = 1
        post_data[cherry_key] = 1
        post_data[taxes_key] = 1
        post_data[other_key] = 1

        self.assertPost(update_url, post_data)

        season_expenses = rw2010.get_expense_tree()
        self.assertEquals(4, len(season_expenses))
        self.assertTrue(self.expense_washing_station in season_expenses)
        self.assertTrue(self.expense_cherry_advance in season_expenses)
        self.assertTrue(self.expense_other in season_expenses)
        self.assertTrue(self.expense_taxes in season_expenses)

    def test_unicode(self):
        season = Season.objects.create(name='2008', country=self.rwanda, 
                                       exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                       farmer_income_baseline=Decimal("100"),
                                       fob_price_baseline=Decimal("1.15"),                                               
                                       created_by=self.admin, modified_by=self.admin)
        self.assertEquals("Rwanda 2008", str(season))
        

    def test_get_grade_tree(self):
        season = Season.objects.create(name='2008', country=self.rwanda, 
                                       exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                       farmer_income_baseline=Decimal("100"), fob_price_baseline=Decimal("1.15"),                                               
                                       created_by=self.admin, modified_by=self.admin)

        season.add_grade(self.ungraded)
        season.add_grade(self.parchment)
        season.add_grade(self.cherry)
        season.add_grade(self.green)
        season.add_grade(self.green15)
        season.add_grade(self.green13)
        season.add_grade(self.low)

        tree = season.get_grade_tree()
        self.assertEquals(7, len(tree))
        self.assertEquals(self.cherry, tree[0])
        self.assertEquals(self.parchment, tree[1])
        self.assertEquals(self.green, tree[2])
        self.assertEquals(self.green15, tree[3])
        self.assertEquals(self.green13, tree[4])
        self.assertEquals(self.low, tree[5])
        self.assertEquals(self.ungraded, tree[6])

    def test_season_attributes(self):
        self.login(self.admin)

        update_url = reverse('seasons.season_update', args=[self.rwanda_2010.id])
        response = self.client.get(update_url)

        cu_second_key = 'cashuse__%d' % self.cu_second_payment.id
        fp_dividend_key = 'payment__%d' % self.fp_dividend.id
        cs_wcap_key = 'cashsource__%d' % self.unused_working_cap.id

        form_fields = response.context['form'].fields
        self.assertTrue(cu_second_key in form_fields)
        self.assertTrue(fp_dividend_key in form_fields)
        self.assertTrue(cs_wcap_key in form_fields)

        post_data = dict(has_members=1, name="2010", country=self.rwanda.id, 
                         exchange_rate="585", default_adjustment=("0.16"),
                         farmer_income_baseline="100", fob_price_baseline="1.15",
                         farmer_payment_left="0", farmer_payment_right="0",
                         cherry_ratio_left="0", cherry_ratio_right="0",
                         total_costs_left="0", total_costs_right="0",
                         sale_price_left="0", sale_price_right="0")

        post_data[cu_second_key] = 1
        post_data[cs_wcap_key] = 1
        post_data[fp_dividend_key] = 'MEM'

        self.assertPost(update_url, post_data)

        # check that our cashuses for the season were updated
        cashuses = self.rwanda_2010.get_cash_uses()
        self.assertEquals(1, len(cashuses))
        self.assertEquals(self.cu_second_payment, cashuses[0])

        cashsources = self.rwanda_2010.get_cash_sources()
        self.assertEquals(1, len(cashsources))
        self.assertEquals(self.unused_working_cap, cashsources[0])

        payments = self.rwanda_2010.get_farmer_payments()
        self.assertEquals(1, len(payments))
        self.assertEquals(self.fp_dividend, payments[0])
        self.assertEquals('MEM', payments[0].applies_to)

        # check our initial data
        response = self.client.get(update_url)

        self.assertContains(response, self.cu_second_payment.name)
        self.assertContains(response, self.fp_dividend.name)
        self.assertContains(response, self.unused_working_cap.name)

        # update our values
        post_data[cu_second_key] = 0
        post_data[fp_dividend_key] = 'MEM'

        self.assertPost(update_url, post_data)

        payments = self.rwanda_2010.get_farmer_payments()
        self.assertEquals(1, len(payments))
        self.assertEquals(self.fp_dividend, payments[0])
        
    def test_season_grades(self):
        self.login(self.admin)
        Season.objects.all().delete()

        # add a grade under cherry
        self.unwashed = Grade.objects.create(name="Unwashed", parent=self.cherry, kind='CHE', order=0,
                                             created_by=self.admin, modified_by=self.admin)
        self.washed = Grade.objects.create(name="Washed", parent=self.cherry, kind='CHE', order=1,
                                           created_by=self.admin, modified_by=self.admin)

        rwanda_2020 = Season.objects.create(name="2020", country=self.rwanda, 
                                            exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                            farmer_income_baseline=Decimal("100"),
                                            fob_price_baseline=Decimal("1.15"),                                               
                                            created_by=self.admin, modified_by=self.admin)
        
        update_url = reverse('seasons.season_update', args=[rwanda_2020.id])
        response = self.client.get(update_url)
        
        green_key = 'grade__%d' % self.green.id
        green_key_top = 'grade__%d__top' % self.green.id
        ungraded_key = 'grade__%d' % self.ungraded.id
        ungraded_key_top = 'grade__%d__top' % self.ungraded.id
        parchment_key = 'grade__%d' % self.parchment.id
        parchment_key_top = 'grade__%d__top' % self.parchment.id

        washed_key = 'grade__%d' % self.washed.id

        form_fields = response.context['form'].fields
        self.assertTrue(green_key in form_fields)
        self.assertFalse(green_key_top in form_fields)
        self.assertTrue(ungraded_key in form_fields)
        self.assertTrue(ungraded_key_top in form_fields)
        self.assertTrue(parchment_key in form_fields)
        self.assertFalse(parchment_key_top in form_fields)

        self.assertTrue(washed_key in form_fields)

        post_data = dict(name="2020", country=self.rwanda.id, exchange_rate="585", default_adjustment="0.16",
                         farmer_income_baseline="100", fob_price_baseline="1.15",
                         farmer_payment_left="0", farmer_payment_right="0",
                         cherry_ratio_left="0", cherry_ratio_right="0",
                         total_costs_left="0", total_costs_right="0",
                         sale_price_left="0", sale_price_right="0")

        post_data[green_key] = 1
        post_data[parchment_key] = 1
        post_data[ungraded_key_top] = 1
        post_data[ungraded_key] = 1
        post_data[washed_key] = 1

        self.assertPost(update_url, post_data)

        season_grades = rwanda_2020.get_grade_tree()
        self.assertEquals(6, len(season_grades))
        self.assertEquals(self.cherry, season_grades[0])
        self.assertEquals(self.washed, season_grades[1])
        self.assertEquals(self.parchment, season_grades[2])
        self.assertEquals(self.green, season_grades[3])
        self.assertEquals(self.low, season_grades[4])
        self.assertEquals(self.ungraded, season_grades[5])
        self.assertTrue(season_grades[5].is_top_grade)

        response = self.client.get(update_url)
        self.assertTrue(response.context['form'].initial[parchment_key])
        self.assertTrue(response.context['form'].initial[ungraded_key_top])

        del post_data[parchment_key]
        self.assertPost(update_url, post_data)

        season_grades = rwanda_2020.get_grade_tree()
        self.assertEquals(5, len(season_grades))
        self.assertEquals(self.cherry, season_grades[0])
        self.assertEquals(self.washed, season_grades[1])
        self.assertEquals(self.green, season_grades[2])
        self.assertEquals(self.low, season_grades[3])
        self.assertEquals(self.ungraded, season_grades[4])

        self.green.is_active = False
        self.green.save()
        response = self.client.get(update_url)
        self.assertNotIn(green_key, response.context['form'].fields)

    def test_seasons_standards(self):
        self.login(self.admin)
        Season.objects.all().delete()
        
        rwanda_2020 = Season.objects.create(name="2020", country=self.rwanda, 
                                            exchange_rate=Decimal("585"), default_adjustment=Decimal("0.16"),
                                            farmer_income_baseline=Decimal("100"),
                                            fob_price_baseline=Decimal("1.15"),                                               
                                            created_by=self.admin, modified_by=self.admin)
        
        update_url = reverse('seasons.season_update', args=[rwanda_2020.id])
        response = self.client.get(update_url)
        
        standard_one_key = 'standard__%d' % self.child_labour.id
        standard_two_key = 'standard__%d' % self.forced_labour.id
        standard_three_key = 'standard__%d' % self.meetings.id
        standard_four_key = 'standard__%d' % self.hazards.id

        form_fields = response.context['form'].fields
        self.assertIn(standard_one_key, form_fields)
        self.assertIn(standard_two_key, form_fields)
        self.assertIn(standard_three_key, form_fields)
        self.assertIn(standard_four_key, form_fields)

        post_data = dict(name="2020",country=self.rwanda.id, exchange_rate="585", default_adjustment="0.16",
                         farmer_income_baseline="100", fob_price_baseline="1.15",
                         farmer_payment_left="0", farmer_payment_right="0",
                         cherry_ratio_left="0", cherry_ratio_right="0",
                         total_costs_left="0", total_costs_right="0",
                         sale_price_left="0", sale_price_right="0")
        post_data[standard_one_key] = 1
        post_data[standard_four_key] = 1
        
        self.assertPost(update_url, post_data)
        
        season_standards = rwanda_2020.standards.all()
        self.assertEquals(2, len(season_standards))
        self.assertEquals(self.child_labour, season_standards[0])
        self.assertEquals(self.hazards, season_standards[1])

        response = self.client.get(update_url)
        self.assertTrue(response.context['form'].initial[standard_one_key])

        del post_data[standard_one_key]
        self.assertPost(update_url, post_data)
        
        season_standards = rwanda_2020.standards.all()
        self.assertEquals(1, len(season_standards))
        self.assertEquals(self.hazards, season_standards[0])
        
        self.hazards.is_active = False
        self.hazards.save()
        
        response = self.client.get(update_url)
        self.assertNotIn(standard_four_key, response.context['form'].fields)


    def test_season_cloning(self):
        """
        Tests that seasons inherit the settings from the previous season when they 
        are first created.
        """
        self.login(self.admin)
        
        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.green15, True)

        self.rwanda_2010.add_expense(self.expense_washing_station)
        self.rwanda_2010.add_expense(self.expense_other, True)

        self.rwanda_2010.add_cash_use(self.cu_dividend)
        self.rwanda_2010.add_cash_source(self.unused_working_cap)
        self.rwanda_2010.add_standard(self.child_labour)
        self.rwanda_2010.add_farmer_payment(self.fp_second_payment, 'MEM')

        # blow away the kenya season, we want to test what happens with a clone with no prior seasons
        Season.objects.filter(country=self.kenya).delete()

        post_data = dict(name="2020",
                         country=self.kenya.id)

        response = self.client.post(reverse('seasons.season_clone'), post_data)
        self.assertRedirect(response, reverse('seasons.season_create'))

        response = self.client.get(response.get('Location', None))

        self.assertEquals("2020", response.context['form'].initial['name'])
        self.assertEquals(self.kenya, response.context['form'].initial['country'])

        # ok, now do it for rwanda, where we will clone normally
        post_data = dict(name="2020",
                         country=self.rwanda.id)

        response = self.client.post(reverse('seasons.season_clone'), post_data)
        season = Season.objects.get(name="2020")
        self.assertRedirect(response, reverse('seasons.season_update', args=[season.id]))

        # should have the same settings as Rwanda 2010
        rw2010 = self.rwanda_2010

        exp10 = rw2010.get_expense_tree()
        exp20 = season.get_expense_tree()

        self.assertEquals(len(exp10), len(exp20))

        for i in range(len(exp10)):
            self.assertEquals(exp10[i].pk, exp20[i].pk)
            self.assertEquals(exp10[i].collapse, exp20[i].collapse)

        gr10 = rw2010.get_grade_tree()
        gr20 = season.get_grade_tree()

        self.assertEquals(len(gr10), len(gr20))

        for i in range(len(gr10)):
            self.assertEquals(gr10[i].pk, gr20[i].pk)
            self.assertEquals(gr10[i].is_top_grade, gr20[i].is_top_grade)

        cu10 = rw2010.get_cash_uses()
        cu20 = season.get_cash_uses()

        self.assertEquals(len(cu10), len(cu20))

        for i in range(len(cu10)):
            self.assertEquals(cu10[i].pk, cu20[i].pk)

        cs10 = rw2010.get_cash_sources()
        cs20 = season.get_cash_sources()

        self.assertEquals(len(cs10), len(cs20))

        for i in range(len(cs10)):
            self.assertEquals(cs10[i].pk, cs20[i].pk)

        fp10 = rw2010.get_farmer_payments()
        fp20 = season.get_farmer_payments()

        self.assertEquals(len(fp10), len(fp20))

        for i in range(len(fp10)):
            self.assertEquals(fp10[i].pk, fp20[i].pk)

        st10 = rw2010.get_standards()
        st20 = season.get_standards()
        
        self.assertEquals(len(st10), len(st20))

        for i in range(len(st10)):
            self.assertEquals(st10[i].pk, st20[i].pk)

        # check our gauge fields
        fields = ('exchange_rate', 'default_adjustment', 'has_local_sales', 'has_members', 'has_misc_revenue',
                  'farmer_income_baseline', 'fob_price_baseline',
                  'sale_price_left', 'sale_price_right', 'total_costs_left', 'total_costs_right',
                  'cherry_ratio_left', 'cherry_ratio_right', 'farmer_payment_left', 'farmer_payment_right')
        for field in fields:
            self.assertEquals(getattr(rw2010, field, None), getattr(season, field, None))

    test_season_cloning.active = True
