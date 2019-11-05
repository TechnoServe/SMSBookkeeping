# -*- coding: utf-8 -*-
from django.test import TestCase
from .models import *
from tns_glass.tests import TNSTestCase
from decimal import Decimal
from templatetags.locales import *
from django.core.urlresolvers import reverse
import datetime

class FormatTest(TNSTestCase):

    def test_formatted(self):
        self.assertEqual("1,000", comma_formatted(Decimal(1000), False))
        self.assertEqual("1,000.00", comma_formatted(Decimal(1000), True))
        self.assertEqual("1,010.20", comma_formatted(Decimal("1010.20"), True))
        self.assertEqual("1,010", comma_formatted(Decimal("1010"), False))

        self.assertEqual("-1,010", comma_formatted(Decimal("-1010"), False))

        self.assertEqual("-1,010,200", comma_formatted(Decimal("-1010200"), False))

        self.assertEqual("38.23", comma_formatted(Decimal("38.23"), True))

    def test_templatetags(self):
        self.assertEqual("333 333", format_string("### ###", "333333"))
        self.assertEqual("333-333", format_string("###-###", "333333"))

        # wrong number of args should back down to original format
        self.assertEqual("33333", format_string("###-###", "33333"))

        country = Country()
        country.phone_format = '#### ## ## ##'

        self.assertEquals("0788 38 33 83", format_phone('0788383383', country))
        self.assertEquals("078838338", format_phone('078838338', country))

        country.national_id_format = '#-####-#-#######-#-##'

        self.assertEquals("1-1984-8-0004007-0-52", format_id('1198480004007052', country))
        self.assertEquals("119844804007052", format_id('119844804007052', country))

        # this time is assumed to be in UTC
        time = datetime.datetime(day=23, month=6, year=1977, hour=10, minute=30, second=0)
        
        # but we want it displayed in the local timezone, CAT, which is +2
        self.assertEquals("Jun 23 1977, 12:30", local_timezone(time))

        # int formatting
        self.assertEquals("1,234", format_int(1234))
        self.assertEquals("1,234", format_int(Decimal("1234.00")))
        self.assertEquals("12.00.00", format_int("12.00.00"))

        # currency formatting
        self.assertEquals("$12.00", format_currency(Decimal("12"), self.usd))
        self.assertEquals("12.00.00", format_currency("12.00.00", self.usd))

class CurrencyTest(TNSTestCase):

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('locales.currency_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        post_data = dict(name="Euro",
                         currency_code='EUR',
                         abbreviation='EUR',
                         has_decimals=True,
                         prefix="€",
                         suffix="")

        response = self.assertPost(reverse('locales.currency_create'), post_data)
        self.assertAtURL(response, reverse('locales.currency_list'))
        currency = Currency.objects.get(currency_code='EUR')

        update_url = reverse('locales.currency_update', args=[currency.id])
        response = self.client.get(update_url)
        post_data = response.context['form'].initial
        post_data['name'] = "European Euro"
        self.assertEqual(currency.format(5).encode('utf8'), '€5.00')
        
        self.assertPost(update_url, post_data)
        currency = Currency.objects.get(currency_code='EUR')
        self.assertEquals("European Euro", currency.name)

        response = self.client.get(reverse('locales.currency_list'))
        self.assertContains(response, "European Euro")

class WeightTest(TNSTestCase):

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('locales.weight_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        post_data = dict(name="Quintalatium",
                         abbreviation="Qt",
                         ratio_to_kilogram=135)

        response = self.assertPost(reverse('locales.weight_create'), post_data)
        self.assertAtURL(response, reverse('locales.weight_list'))
        weight = Weight.objects.get(name="Quintalatium")
        self.assertEquals(weight.ratio_to_kilogram, 135)

        update_url = reverse('locales.weight_update', args=[weight.id])
        response = self.client.get(update_url)
        post_data = response.context['form'].initial
        post_data['name'] = 'Quintales'
        post_data['ratio_to_kilogram'] = 150

        self.assertPost(update_url, post_data)
        weight = Weight.objects.get(abbreviation='Qt')
        self.assertEquals("Quintales", weight.name)
        self.assertEquals(150, weight.ratio_to_kilogram)

        response = self.client.get(reverse('locales.weight_list'))
        self.assertContains(response, "Quintales")


class CountryTest(TNSTestCase):

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('locales.country_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        post_data = dict(name="France",
                         country_code='FR',
                         currency=self.rwf.id,
                         weight=self.kilogram.id,
                         language='en_us',
                         calling_code='33',
                         phone_format='### ### ####',
                         national_id_format='#### ####',
                         bounds_zoom='6',
                         bounds_lat='1.33025',
                         bounds_lng='32.708514')

        self.assertPost(reverse('locales.country_create'), post_data)
        country = Country.objects.get(country_code='FR')

        update_url = reverse('locales.country_update', args=[country.id])
        self.client.get(update_url)
        post_data['name'] = "La France"

        post_data['bounds_lat'] = ''
        post_data['bounds_lng'] = ''

        # should fail because there are no bounds
        response = self.client.post(update_url, post_data)
        self.assertEquals(200, response.status_code)
        self.assertTrue('form' in response.context)

        post_data['bounds_lat'] = '-1.33025'
        post_data['bounds_lng'] = '29.3454'

        self.assertPost(update_url, post_data)
        country = Country.objects.get(country_code='FR')
        self.assertEquals("La France", country.name)

        response = self.client.get(reverse('locales.country_list'))
        self.assertContains(response, "La France")

class ProvinceTest(TNSTestCase):

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('locales.province_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        
        post_data = dict(name="Kasai",
                         country = self.rwanda.id,
                         order='1')

        self.assertPost(reverse('locales.province_create'), post_data)
        province = Province.objects.get(name='Kasai')
        
        update_url = reverse('locales.province_update', args=[province.id])
        self.client.get(update_url)
        post_data['name'] = "Rubumbashi"
        
        self.assertPost(update_url, post_data)
        province = Province.objects.get(name="Rubumbashi")
        self.assertEquals("Rubumbashi", province.name)

        response = self.client.get(reverse('locales.province_list'))
        self.assertContains(response, "Rubumbashi")


    def test_ordering(self):
        northern = Province.objects.create(name="Northern", country=self.rwanda, order=0, 
                                           created_by=self.admin, modified_by=self.admin)
        kigali = Province.objects.create(name="Kigali", country=self.rwanda, order=3, 
                                         created_by=self.admin, modified_by=self.admin)
        southern = Province.objects.create(name="Southern", country=self.rwanda, order=5, 
                                           created_by=self.admin, modified_by=self.admin)

        central = Province.objects.create(name="Central", country=self.kenya, order=4, 
                                          created_by=self.admin, modified_by=self.admin)
        eastern = Province.objects.create(name="Eastern", country=self.kenya, order=1, 
                                          created_by=self.admin, modified_by=self.admin)

        self.login(self.admin)
        response = self.client.get(reverse('locales.province_list'))

        # make sure our locales are in order 
        provinces = response.context['province_list']

        self.assertEquals(self.kibirira, provinces[0])
        self.assertEquals(eastern, provinces[1])
        self.assertEquals(self.mucoma, provinces[2])
        self.assertEquals(central, provinces[3])
        self.assertEquals(northern, provinces[4])
        self.assertEquals(self.gitega, provinces[5])
        self.assertEquals(self.bwanacyambwe, provinces[6])
        self.assertEquals(kigali, provinces[7])
        self.assertEquals(southern, provinces[8])

class NavigationTestCase(TNSTestCase):

    def test_admin_links(self):
        self.login(self.admin)

        response = self.client.get(reverse('locales.country_list'))
        self.assertContains(response, reverse('locales.country_list'))
        self.assertContains(response, reverse('locales.currency_list'))
        self.assertContains(response, reverse('locales.province_list'))
        

        
