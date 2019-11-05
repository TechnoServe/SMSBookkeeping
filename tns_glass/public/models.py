from django.db import models
from locales.models import Currency, Country, Weight
from wetmills.models import Wetmill
from seasons.models import Season
from reports.models import Report

def get_report_currencies(country, currency_code):
    return [country.currency, Currency.objects.get(currency_code__iexact=currency_code)]

def get_report_weights(country, weight_abbreviation):
    return [country.weight, Weight.objects.get(abbreviation__iexact=weight_abbreviation)]

def get_total_farmers(country=None):
    if not country:
        countries = Country.objects.all()
    else:
        countries = [country]

    farmer_count = 0
    for country in countries:
        season = Season.objects.filter(is_finalized=True, is_active=True, country=country).order_by('-name')
        if season:
            aggregate = Report.objects.filter(is_active=True, season=season[0])
            aggregate = aggregate.aggregate(models.Sum('farmers'))
            farmers_sum = aggregate.get('farmers__sum', 0)

            if farmers_sum:
                farmer_count += farmers_sum

    return farmer_count

def get_total_wetmills(country=None):
    wetmills = Wetmill.objects.filter(is_active=True)

    if country:
        wetmills = wetmills.filter(country=country)

    return wetmills.count()
