from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from locales.models import Country, Currency
from wetmills.models import Wetmill
from seasons.models import Season
from standards.models import StandardCategory
from .models import *
from django.core.urlresolvers import reverse
from sms.views import add_sms_data_to_context

def home(request):
    farmer_count = get_total_farmers()
    wetmill_count = get_total_wetmills()

    context = dict(farmer_count=farmer_count, wetmill_count=wetmill_count)

    return render_to_response('public/home.html', context, context_instance=RequestContext(request))

def country_home(request, country_code):
    country = Country.objects.get(country_code__iexact=country_code)
    wetmills = Wetmill.objects.filter(country=country, is_active=True)

    onethird = len(wetmills) / 3
    twothird = onethird * 2

    left = wetmills[:onethird]
    center = wetmills[onethird:twothird]
    right = wetmills[twothird:]

    farmer_count = get_total_farmers(country)
    wetmill_count = get_total_wetmills(country)

    context = dict(country=country, wetmills=wetmills, left=left, center=center, right=right,
                   farmer_count=farmer_count, wetmill_count=wetmill_count)
    return render_to_response('public/country.html', context, context_instance=RequestContext(request))

def wetmill_home(request, wetmill_id):
    wetmill = Wetmill.objects.get(pk=wetmill_id)
    seasons = Season.objects.filter(country=wetmill.country, is_active=True)

    finalized_reports = []
    for report in wetmill.reports.all():
        if report.is_finalized:
            finalized_reports.append(report)

    last_report = wetmill.get_most_recent_transparency_report()

    finalized_scorecards = []
    for scorecard in wetmill.scorecards.all():
        if scorecard.is_finalized:
            finalized_scorecards.append(scorecard)

    last_scorecard = wetmill.get_most_recent_scorecard()
    if last_scorecard:
        display_categories = []
        metrics = last_scorecard.calculate_metrics()
        for (acronym, score) in metrics.items():
            category = StandardCategory.objects.get(acronym=acronym)
            if category.public_display:
                category.score = score[1]
                display_categories.append(category)

        last_scorecard.display_categories = display_categories

    # build our list of currencies for the report
    country = wetmill.country
    currencies = get_report_currencies(country, "USD")

    languages = []
    languages.append(dict(name="English", language_code="en_us"))

    # get our sms system for our last season
    accounting_system = 'NONE'
    if seasons:
        accounting_system = wetmill.get_accounting_for_season(seasons[0])

    context = dict(wetmill=wetmill,
                   seasons=seasons,
                   country=country,
                   currencies=currencies,
                   languages=languages,
                   finalized_reports=finalized_reports,
                   finalized_scorecards=finalized_scorecards,
                   last_report=last_report,
                   last_scorecard=last_scorecard,
                   accounting_system=accounting_system,
                   usd=Currency.objects.get(currency_code='USD'))
    return render_to_response('public/wetmill.html', context, context_instance=RequestContext(request))

def search(request):
    query = request.REQUEST.get('query', None)
    country_code = request.REQUEST.get('country', None)

    wetmills = Wetmill.objects.filter(is_active=True)

    country = None
    if country_code:
        country = Country.objects.get(country_code__iexact=country_code)
        wetmills = wetmills.filter(country=country)

    if query:
        terms = query.split()
        for term in terms:
            wetmills = wetmills.filter(name__icontains=term.lower())

    # single result?  go straight there
    if wetmills.count() == 1:
        return HttpResponseRedirect(reverse("public-wetmill", args=[wetmills[0].id]))
    else:
        wetmills = wetmills.order_by('name')[:25]
        context = dict(wetmills=wetmills, country=country, query=query)
        return render_to_response('public/search.html', context, context_instance=RequestContext(request))
