from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from guardian.shortcuts import get_objects_for_user
from lxml.cssselect import CSSSelector
import requests
import re

from wetmills.models import Wetmill, WetmillCSPSeason
from seasons.models import Season
from sms.models import *
from smartmin.models import SmartModel
from django.db.models import Sum, Max, Count, Min, Q

from datetime import date
from datetime import datetime
import pytz
import time

from lxml.html import fromstring
from django.utils.translation import ugettext_lazy as _


def calculate_cherry_ytd(season, wetmill_ids, until_date=None):
    # If until_date is set, it overrides the ytd (Year to Date) and brings data only until the specified date.

    if until_date is None:
        sums = IbitumbweSubmission.objects.filter(season=season, active=True, wetmill__in=wetmill_ids).order_by('wetmill').values('wetmill').annotate(Sum('cherry_purchased'), Sum('cash_spent'), Sum('credit_spent'), Max('report_day'), Min('report_day'))
    else:
        sums = IbitumbweSubmission.objects.filter(season=season, active=True, wetmill__in=[wetmill_ids, ], report_day__lte=until_date).order_by('wetmill').values('wetmill').annotate(Sum('cherry_purchased'), Sum('cash_spent'), Sum('credit_spent'), Max('report_day'), Min('report_day'))

    values = dict()
    for cherry in sums:
        spent_ytd = cherry['cash_spent__sum'] + cherry['credit_spent__sum']
        cherry_ytd = cherry['cherry_purchased__sum']

        cherry_price = None
        if cherry_ytd > Decimal(0):
            cherry_price = spent_ytd / cherry_ytd

        cherry_tons_ytd = (cherry_ytd / Decimal("1000")).quantize(Decimal(".1"))

        values[cherry['wetmill']] = dict(cherry_date_first=cherry['report_day__min'],
                                         cherry_date_last=cherry['report_day__max'],
                                         cherry_ytd=cherry_ytd,
                                         cherry_tons_ytd=cherry_tons_ytd,
                                         cherry_spent_ytd=spent_ytd,
                                         cherry_price_ytd=cherry_price)

    return values

def calculate_parchment_stats(season, wetmill_ids, until_date=None):
    # If until_date is set, it overrides the ytd and brings data only until the specified date.
    if until_date is None:
        sums = SitokiSubmission.objects.filter(season=season, active=True, wetmill__in=wetmill_ids).order_by('wetmill').values('wetmill').annotate(Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'), Sum('grade_a_shipped'), Sum('grade_b_shipped'), Sum('grade_c_shipped'))
    else:
        sums = SitokiSubmission.objects.filter(season=season, active=True, wetmill__in=[wetmill_ids, ], start_of_week__lte=until_date).order_by('wetmill').values('wetmill').annotate(Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'), Sum('grade_a_shipped'), Sum('grade_b_shipped'), Sum('grade_c_shipped'))

    parchment_data = dict()
    for parchment in sums:
        stored = parchment['grade_a_stored__sum'] + parchment['grade_b_stored__sum'] + parchment['grade_c_stored__sum']
        shipped = parchment['grade_a_shipped__sum'] + parchment['grade_b_shipped__sum'] + parchment['grade_c_shipped__sum']
        in_store = stored - shipped

        stored_tons = (stored / Decimal("1000")).quantize(Decimal(".1"))
        in_store_tons = (in_store / Decimal("1000")).quantize(Decimal(".1"))

        if stored > Decimal(0):
            percent_of_parchment_shipped = shipped * Decimal("100") / Decimal(stored)
        else:
            percent_of_parchment_shipped = Decimal(0)

        parchment_data[parchment['wetmill']] = dict(parchment_tons_stored_ytd=stored_tons,
                                                    parchment_stored_ytd=stored,
                                                    parchment_shipped_ytd=shipped,
                                                    parchment_in_store=in_store,
                                                    parchment_in_store_tons=in_store_tons,
                                                    percent_of_parchment_shipped=percent_of_parchment_shipped)
    return parchment_data

def calculate_parchment_estimates(stock_data, exchange_rate):
    for wetmill_data in stock_data:
        if 'parchment_shipped_ytd' in wetmill_data:
            assumptions = wetmill_data['assumptions']
            shipped = wetmill_data['parchment_shipped_ytd']
            stored = wetmill_data['parchment_stored_ytd']

            cherry_parchment_ratio = assumptions.cherry_parchment_ratio
            est_parchment_processed = wetmill_data.get('cherry_ytd', Decimal(0)) / cherry_parchment_ratio
            est_parchment_tabled = est_parchment_processed - shipped- wetmill_data['parchment_in_store']

            # get the latest price
            price = NYCherryPrice.objects.filter(is_active=True).order_by('-date')
            if price:
                est_stored_parchment_value = (stored / assumptions.parchment_green_ratio) * (price[0].price + assumptions.green_price_differential) * exchange_rate
                est_total_parchment_value = (est_parchment_processed/assumptions.parchment_green_ratio) * (price[0].price + assumptions.green_price_differential) * exchange_rate
                wetmill_data['est_stored_parchment_value'] = est_stored_parchment_value
                wetmill_data['est_total_parchment_value'] = est_total_parchment_value

            wetmill_data['cherry_parchment_ratio'] = cherry_parchment_ratio
            wetmill_data['est_parchment_processed'] = est_parchment_processed
            wetmill_data['est_parchment_tabled'] = est_parchment_tabled

def find_active_wetmills(season, wetmills):
    wetmill_ids = set([w.pk for w in wetmills])

    # only include wetmills that have at least one cherry submission
    active_wetmills = set([s['wetmill'] for s in IbitumbweSubmission.objects.filter(season=season, wetmill__in=wetmill_ids).order_by('wetmill').values('wetmill').distinct()])

    inactive_wetmills = wetmill_ids.difference(active_wetmills)

    return Wetmill.objects.filter(id__in=active_wetmills), Wetmill.objects.filter(id__in=inactive_wetmills)

def load_assumptions_for_wetmills(season, wetmills, user):
    wetmill_ids = [w.id for w in wetmills]
    wetmill_assumptions = dict()

    season_assumptions = Assumptions.for_csp(season, None, user)

    # load all our csp assumptions
    csp_assumptions = dict()
    for assumption in Assumptions.objects.filter(season=season, wetmill=None).exclude(csp=None):
        assumption.set_defaults(season_assumptions)
        csp_assumptions[assumption.csp_id] = assumption

    # cache all our csps for this season
    wetmill_csp_mappings = dict()
    for wetmill_csp in WetmillCSPSeason.objects.filter(season=season).select_related('csp', 'wetmill'):
        wetmill_csp_mappings[wetmill_csp.wetmill.id] = wetmill_csp.csp_id

    # load all our wetmill assumptions
    for assumption in Assumptions.objects.filter(season=season, wetmill__in=wetmill_ids):
        csp = wetmill_csp_mappings.get(assumption.wetmill_id, -1)
        if csp in csp_assumptions:
            assumption.set_defaults(csp_assumptions[csp])
        else:
            assumption.set_defaults(season_assumptions)

        wetmill_assumptions[assumption.wetmill_id] = assumption

    # now fill in the gaps with csp or season assumptions
    csp_assumptions = dict()
    for wetmill in wetmills:
        if wetmill.id not in wetmill_assumptions:
            csp = wetmill_csp_mappings.get(wetmill.id, -1)
            if csp in csp_assumptions:
                assumptions = csp_assumptions[csp]
            else:
                assumptions = season_assumptions

            wetmill_assumptions[wetmill.id] = assumptions

    return wetmill_assumptions

def load_assumptions_for_wetmills_by_id(season, wetmill_ids, user):
    wetmill_assumptions = dict()

    season_assumptions = Assumptions.for_csp(season, None, user)

    # load all our csp assumptions
    csp_assumptions = dict()
    for assumption in Assumptions.objects.filter(season=season, wetmill=None).exclude(csp=None):
        assumption.set_defaults(season_assumptions)
        csp_assumptions[assumption.csp_id] = assumption

    # cache all our csps for this season
    wetmill_csp_mappings = dict()
    for wetmill_csp in WetmillCSPSeason.objects.filter(season=season).select_related('csp', 'wetmill'):
        wetmill_csp_mappings[wetmill_csp.wetmill.id] = wetmill_csp.csp_id

    # load all our wetmill assumptions
    for assumption in Assumptions.objects.filter(season=season, wetmill__in=wetmill_ids):
        csp = wetmill_csp_mappings.get(assumption.wetmill_id, -1)
        if csp in csp_assumptions:
            assumption.set_defaults(csp_assumptions[csp])
        else:
            assumption.set_defaults(season_assumptions)

        wetmill_assumptions[assumption.wetmill_id] = assumption

    # now fill in the gaps with csp or season assumptions
    csp_assumptions = dict()
    for wetmill_id in wetmill_ids:
        if wetmill_id not in wetmill_assumptions:
            csp = wetmill_csp_mappings.get(wetmill_id, -1)
            if csp in csp_assumptions:
                assumptions = csp_assumptions[csp]
            else:
                assumptions = season_assumptions

            wetmill_assumptions[wetmill_id] = assumptions

    return wetmill_assumptions



def build_stock_data(season, wetmills, today, user):
    stock_fields = []
    stock_data = []

    stock_fields.append(dict(slug='cherry_last', label=_("Last Cherry"), help=_("Volume Cherry Purchased according to Last Daily Cherry Report")))
    stock_fields.append(dict(slug='cherry_ytd', label=_("Cherry YTD"), help=_("Total Cherry Purchased according to Daily Cherry Reports")))
    stock_fields.append(dict(slug='parchment_shipped_ytd', label=_("Parchment Delivered"), help=_("Total parchment reported delivered in Weekly Stock Messages")))
    stock_fields.append(dict(slug='parchment_in_store', label=_("Parchment in Store"), help=_("Total parchment reported in storage - parchment delivered in Weekly Stock Messages")))
    stock_fields.append(dict(slug='est_parchment_tabled', label=_("Est. Parchment on Tables"), help=_("Total Cherry &divide; 5.2 = Est. Total Parchment\n- Parchment Delivered\n- Parchment in Storage\n= Est. Parchment on tables")))
    stock_fields.append(dict(slug='est_parchment_processed', label=_("Est. Parchment Processed"), help=_("Total Cherry &divide; 5.2 = Est. Total Parchment")))

    wetmill_ids = [w.pk for w in wetmills]

    cherry_last = calculate_cherry_last(season, wetmill_ids)
    cherry_ytd = calculate_cherry_ytd(season, wetmill_ids)
    sitoki_last = calculate_sitoki_last(season, wetmill_ids)
    parchment_ytd = calculate_parchment_stats(season, wetmill_ids)
    assumptions = load_assumptions_for_wetmills(season, wetmills, user)

    # cache all our csps for this season
    wetmill_csp_mappings = dict()
    for wetmill_csp in WetmillCSPSeason.objects.filter(season=season).select_related('csp', 'wetmill'):
        wetmill_csp_mappings[wetmill_csp.wetmill.id] = wetmill_csp.csp

    for wetmill in wetmills:
        wetmill_data = dict(wetmill=wetmill, assumptions=assumptions.get(wetmill.id), csp=wetmill_csp_mappings.get(wetmill.id, None))

        cherry = cherry_last.get(wetmill.pk)
        if cherry:
            wetmill_data.update(cherry)

        cherry = cherry_ytd.get(wetmill.pk)
        if cherry:
            wetmill_data.update(cherry)

        parchment = parchment_ytd.get(wetmill.pk)
        if parchment:
            wetmill_data.update(parchment)

        sitoki = sitoki_last.get(wetmill.pk)
        if sitoki:
            wetmill_data.update(sitoki)

        stock_data.append(wetmill_data)

    calculate_parchment_estimates(stock_data, season.exchange_rate)

    season_assumptions = Assumptions.get_or_create(season, None, None, user)
    calculate_recommended_prices(season, season_assumptions, stock_data)

    return stock_fields, stock_data

def get_attr(obj, field, default):
    value = getattr(obj, field, None)
    if value is None:
        return default
    else:
        return value

def calculate_recommended_prices(season, season_assumptions, all_data):
    # get the latest price
    price = NYCherryPrice.objects.filter(is_active=True).order_by('-date')
    if not price:
        return

    season_assumptions = Assumptions.objects.get(is_active=True, season=season, csp=None, wetmill=None)
    csp_assumption_cache = dict()
    for ass in Assumptions.objects.filter(is_active=True, season=season, wetmill=None).exclude(csp=None):
        csp_assumption_cache[ass.csp_id] = ass

    price = price[0]
    for wetmill_data in all_data:
        csp = wetmill_data['csp']

        if csp:
            csp_assumptions = csp_assumption_cache.get(csp.id, season_assumptions)
        else:
            csp_assumptions = season_assumptions

        washing_station_costs = get_attr(csp_assumptions, 'washing_stations_costs', get_attr(season_assumptions, 'washing_station_costs', Decimal("0.74")))
        milling_costs = get_attr(csp_assumptions, 'milling', get_attr(season_assumptions, 'milling_costs', Decimal("0.40")))
        working_capital_costs = get_attr(csp_assumptions, 'working_capital_costs', get_attr(season_assumptions, 'working_capital_costs', Decimal("0.16")))
        capex_costs = get_attr(csp_assumptions, 'capex_costs', get_attr(season_assumptions, 'capex_costs', Decimal("0.18")))
        fi_costs = get_attr(csp_assumptions, 'fi_costs', get_attr(season_assumptions, 'fi_costs', Decimal("0.16")))

        assumptions = wetmill_data['assumptions']
        production_costs = get_attr(assumptions, 'washing_station_costs', washing_station_costs) + \
                           get_attr(assumptions, 'milling_costs', milling_costs) + \
                           get_attr(assumptions, 'working_capital_costs', working_capital_costs) + \
                           get_attr(assumptions, 'capex_costs', capex_costs) + \
                           get_attr(assumptions, 'fi_costs', fi_costs)

        cherry_green_ratio = assumptions.cherry_parchment_ratio * assumptions.parchment_green_ratio

        wetmill_data['nyc_price'] = price.price
        wetmill_data['production_costs'] = production_costs
        wetmill_data['cherry_green_ratio'] = cherry_green_ratio.quantize(Decimal(".01"))
        wetmill_data['cherry_price_rec'] = price.calculate_recommended_price(assumptions.green_price_differential,
                                                                             production_costs,
                                                                             cherry_green_ratio,
                                                                             season.exchange_rate)


def calculate_sitoki_last(season, wetmill_ids):
    if not wetmill_ids: return dict()

    sql = "select sms1.* from sms_sitokisubmission as sms1 left join sms_sitokisubmission "\
          "as sms2 on (sms1.wetmill_id = sms2.wetmill_id and sms1.start_of_week < sms2.start_of_week and sms2.is_active=1) "\
          "where sms2.smssubmission_ptr_id is null and sms1.wetmill_id in (%s) and sms1.season_id = %s and sms1.is_active=1" % (",".join([str(w) for w in wetmill_ids]), season.id)

    last_sitoki = IbitumbweSubmission.objects.raw(sql)

    values = dict()
    for sitoki in last_sitoki:
        values[sitoki.wetmill_id] = dict(sitoki_last=sitoki.start_of_week)

    return values

def calculate_cherry_last(season, wetmill_ids):
    if not wetmill_ids: return dict()

    sql = "select sms1.* from sms_ibitumbwesubmission as sms1 left join sms_ibitumbwesubmission " \
    "as sms2 on (sms1.wetmill_id = sms2.wetmill_id and sms1.report_day < sms2.report_day and sms2.is_active=1) " \
    "where sms2.smssubmission_ptr_id is null and sms1.wetmill_id in (%s) and sms1.season_id = %s and sms1.is_active=1" % (",".join([str(w) for w in wetmill_ids]), season.id)

    last_cherry = IbitumbweSubmission.objects.raw(sql)

    values = dict()
    for cherry in last_cherry:
        purchased = cherry.cherry_purchased

        if purchased > Decimal(0):
            cherry_price = (cherry.cash_spent + cherry.credit_spent) / purchased
            values[cherry.wetmill_id] = dict(cash_spent_last=cherry.cash_spent,
                                             credit_spent_last=cherry.credit_spent,
                                             cherry_spent_last=cherry.credit_spent + cherry.cash_spent,
                                             cherry_last=cherry.cherry_purchased,
                                             cherry_price_last=cherry_price,
                                             cherry_date_last=cherry.report_day)

    return values

def calculate_amafaranga_last(season, wetmill_ids):
    if not wetmill_ids: return dict()

    sql = "select sms1.* from sms_amafarangasubmission as sms1 left join sms_amafarangasubmission "\
    "as sms2 on (sms1.wetmill_id = sms2.wetmill_id and sms1.start_of_week < sms2.start_of_week and sms2.is_active=1) "\
    "where sms2.smssubmission_ptr_id is null and sms1.wetmill_id in (%s) and sms1.season_id = %s and sms1.is_active=1" % (",".join([str(w) for w in wetmill_ids]), season.id)

    last_amafaranga = AmafarangaSubmission.objects.raw(sql)

    values = dict()
    for af in last_amafaranga:
        cash_balance = af.opening_balance + af.working_capital + af.other_income - af.advanced - \
              af.full_time_labor - af.casual_labor - af.commission - af.transport - af.other_expenses

        values[af.wetmill_id] = dict(cash_balance=cash_balance,
                                     amafaranga_last=af.start_of_week,
                                     advanced_last=af.advanced,
                                     opening_balance_last=af.opening_balance)

    return values

def calculate_amafaranga_ytd(season, wetmill_ids, until_date=None):

    if until_date is None:
        sums = AmafarangaSubmission.objects.filter(season=season, wetmill__in=wetmill_ids).order_by('wetmill').values('wetmill').annotate(
            Sum('working_capital'), Sum('other_income'), Sum('advanced'), Sum('full_time_labor'),
            Sum('casual_labor'), Sum('commission'), Sum('transport'), Sum('other_expenses'))
    else:
        sums = AmafarangaSubmission.objects.filter(season=season, wetmill__in=wetmill_ids, start_of_week__lte=until_date).order_by('wetmill').values('wetmill').annotate(
            Sum('working_capital'), Sum('other_income'), Sum('advanced'), Sum('full_time_labor'),
            Sum('casual_labor'), Sum('commission'), Sum('transport'), Sum('other_expenses'))

    values = dict()
    for finance in sums:
        op_exp = finance['full_time_labor__sum'] + finance['casual_labor__sum'] + finance['commission__sum'] + finance['transport__sum'] + finance['other_expenses__sum']
        total_exp = finance['advanced__sum'] + finance['full_time_labor__sum'] + finance['casual_labor__sum'] + finance['commission__sum'] + finance['transport__sum'] + finance['other_expenses__sum']
        working_capital = finance['working_capital__sum']

        working_capital_op_exp = None
        working_capital_million_ytd = Decimal(0)

        if working_capital and total_exp > Decimal(0):
            working_capital_op_exp = op_exp * Decimal("100") / total_exp
        working_capital_million_ytd = (working_capital / Decimal("1000000")).quantize(Decimal(".001"))



        values[finance['wetmill']] = dict(working_capital_ytd=working_capital,
                                          working_capital_op_exp=working_capital_op_exp,
                                          working_capital_million_ytd=working_capital_million_ytd,
                                          op_exp_ytd=op_exp,
                                          total_exp_ytd=total_exp)

    return values

def calculate_uncollaterized_working_capital(season, wetmills):
    # Calculated by taking the total "working capital received to date" and subtracting the value
    # of "parchment delivered to csp to date".
    #
    # Value of "parchment delivered to csp to date" calculated by multiplying volume calculated in
    # Stocks tab by value of parchment specified by lender at the beginning of the season
    for wetmill_data in wetmills:
        parchment_shipped = wetmill_data.get('parchment_shipped_ytd', Decimal(0))
        working_capital = wetmill_data.get('working_capital_ytd')
        if working_capital is not None:
            parchment_shipped_value = parchment_shipped * wetmill_data['assumptions'].parchment_value
            wetmill_data['parchment_value'] = wetmill_data['assumptions'].parchment_value
            wetmill_data['working_capital_unc'] = working_capital - parchment_shipped_value

def calculate_estimated_profitability(season, wetmills):
    for wetmill_data in wetmills:
        working_capital = wetmill_data.get('working_capital_ytd')
        est_total_parchment_value = wetmill_data.get('est_total_parchment_value')
        if working_capital > Decimal("0"):
            if est_total_parchment_value is not None:
                est_profitability_ytd = ((est_total_parchment_value / working_capital) - 1) * Decimal("100")
                wetmill_data['est_profitability_ytd'] = est_profitability_ytd
            if wetmill_data['assumptions'].total_working_capital is not None and wetmill_data['assumptions'].total_working_capital > Decimal(0):
                working_capital_received_percent = (working_capital / wetmill_data['assumptions'].total_working_capital) * Decimal("100")
                wetmill_data['working_capital_received_percent'] = working_capital_received_percent

def build_finance_data(season, wetmill_data, wetmills, today, user):
    is_guatemala = season.country.country_code == 'GT'

    wetmill_ids = [w.id for w in wetmills]
    finance_fields = []

    finance_fields.append(dict(slug='cherry_price_ytd', label=_("Avg Cherry Price"), help=_("Average Farmgate Price Paid over season YTD")))
    finance_fields.append(dict(slug='cherry_price_last', label=_("Last Cherry Price"), help=_("Most recent Farmgate price paid according to last Daily Cherry Report")))
    finance_fields.append(dict(slug='cherry_price_rec', label=_("Recommended Cherry price"), help=_("Calculated from NYC - Production Expenses = Recommended Cherry Price\nEdit production costs for all in Global Settings or a specific wetmill in Wetmill Settings")))

    if not is_guatemala:
        finance_fields.append(dict(slug='working_capital_ytd', label=_("Working Capital Received"), help=_("Total Working Capital reported received in Weekly Cash Reports")))

    finance_fields.append(dict(slug='working_capital_op_exp', label=_("% Working Capital on Non-Cherry Expenses"), help=_("% of reported working capital spent on non-cherry operating expenses")))

    if not is_guatemala:
        finance_fields.append(dict(slug='working_capital_unc', label=_("Uncollaterized Working Cap"), help=_("Working Capital Received - est. value of Parchment Delivered\nEdit parchment value for all in Global Settings or a specific wetmill in Wetmill Settings")))

    finance_fields.append(dict(slug='cash_balance', label=_("Cash Balance")))

    amafaranga_data = calculate_amafaranga_ytd(season, wetmill_ids)
    last_amafaranga_data = calculate_amafaranga_last(season, wetmill_ids)

    for data in wetmill_data:
        wetmill = data['wetmill']

        amafaranga = amafaranga_data.get(wetmill.id, None)
        if amafaranga:
            data.update(amafaranga)

        amafaranga = last_amafaranga_data.get(wetmill.id, None)
        if amafaranga:
            data.update(amafaranga)

    calculate_uncollaterized_working_capital(season, wetmill_data)
    calculate_estimated_profitability(season, wetmill_data)

    return finance_fields, wetmill_data

def calculate_ideal_submission_count(season, wetmill, season_start, season_end):
    # we should have at least one submission for ibitumbwe or twakinze per day
    daily_submissions = (season_end - season_start).days + 1

    if season_start.weekday() == 4:
        first_week_report = season_start
    elif season_start.weekday() < 4: # thursday or before means the previous week
        first_week_report = season_start + timedelta(days=4-season_start.weekday()) - timedelta(days=7)
    else: # must be saturday or sunday
        first_week_report = season_start - timedelta(days=season_start.weekday()-4)

    if season_end.weekday() >= 5: # saturday
        last_week_report = season_end - timedelta(days=4-season_end.weekday())
    else: # before then, have to go to the previous friday
        last_week_report = season_end - timedelta(days=season_end.weekday() + 3) - timedelta(days=7)

    weekly_submissions = 0
    if last_week_report > first_week_report:
        weekly_submissions = (last_week_report - first_week_report).days / 7 * 2

    # our first week won't be in the calculation above
    if last_week_report >= first_week_report:
        weekly_submissions += 2

    accounting_system = wetmill.get_accounting_for_season(season)
    if accounting_system == '2012' or accounting_system == 'GTWB':
        return daily_submissions + weekly_submissions
    else:
        return daily_submissions

def calculate_finance_variance(season, wetmill_ids, wetmill_data, today):
    # we know our last amafaranga message, but now need to load the sum of advances for the week prior in ibitumbwe
    # messages the dates are different per wetmill however, so we need to build the SQL ourselves
    from django.db import connection, transaction
    cursor = connection.cursor()

    ibitumbwe_where_clauses = []
    amafaranga_where_clauses = []
    for wetmill in wetmill_data:
        last_amafaranga = wetmill.get('amafaranga_last', None)
        wetmill_id = wetmill['wetmill'].id

        if last_amafaranga:
            start = last_amafaranga
            end = start + timedelta(days=7)
            previous = start - timedelta(days=7)

            start_sql = "date('%d-%d-%d')" % (start.year, start.month, start.day)
            end_sql = "date('%d-%d-%d')" % (end.year, end.month, end.day)

            previous_sql = "date('%d-%d-%d')" % (previous.year, previous.month, previous.day)

            ibitumbwe_where_clauses.append("(wetmill_id = %d and report_day >= %s and report_day < %s and is_active=1)" % (wetmill_id, start_sql, end_sql))
            amafaranga_where_clauses.append("(wetmill_id = %d and start_of_week = %s and is_active=1)" % (wetmill_id, previous_sql))

    # nothing to query, bail
    if not ibitumbwe_where_clauses:
        return

    where_clause = " or ".join(ibitumbwe_where_clauses)
    sql = "select wetmill_id, sum(cash_advanced) from sms_ibitumbwesubmission where %s group by wetmill_id;" % where_clause
    cursor.execute(sql)
    results = cursor.fetchall()

    # convert our results to a map
    week_advanced = dict()
    for row in results:
        week_advanced[row[0]] = row[1]

    # get our previous amafaranga records
    previous_closes = dict()
    for af in AmafarangaSubmission.objects.raw("select * from sms_amafarangasubmission where %s" % " or ".join(amafaranga_where_clauses)):
        previous_closes[af.wetmill_id] = af.opening_balance + af.working_capital + af.other_income - af.advanced - \
                                         af.full_time_labor - af.casual_labor - af.commission - af.transport - af.other_expenses

    # calculate the variance now
    for wetmill in wetmill_data:
        wetmill_id = wetmill['wetmill'].id
        advanced_last = wetmill.get('advanced_last', None)
        advanced_week = week_advanced.get(wetmill_id, Decimal(0))

        if advanced_last is not None:
            wetmill['advanced_week'] = advanced_week
            wetmill['advanced_variance'] = advanced_week - advanced_last

            if advanced_last:
                wetmill['advanced_variance_pct'] = (advanced_week - advanced_last) * Decimal(100) / advanced_last
            elif advanced_last == 0 and advanced_week == 0:
                wetmill['advanced_variance_pct'] = Decimal("0")
            else:
                wetmill['advanced_variance_pct'] = Decimal("100")

        previous_close = previous_closes.get(wetmill_id, None)
        opening_last = wetmill.get('opening_balance_last', None)

        if previous_close is not None and opening_last is not None:
            wetmill['balance_previous_close'] = previous_close
            wetmill['balance_variance'] = opening_last - previous_close

            if opening_last:
                wetmill['balance_variance_pct'] = (opening_last - previous_close) * Decimal(100) / opening_last
            else:
                wetmill['balance_variance_pct'] = Decimal("100")

def calculate_performance_alerts(season, wetmill_datas):

    for wetmill_data in wetmill_datas:
        assumptions = wetmill_data['assumptions']

        wetmill_data['parchment_tabled_alert'] = None
        if not assumptions.alert_parchment_tabled is None:
            actual = wetmill_data.get('est_parchment_tabled', None)

            if actual is not None and actual > assumptions.alert_parchment_tabled:
                wetmill_data['parchment_tabled_alert'] = 'performance-alert'

        wetmill_data['last_cherry_price_alert'] = None
        if not assumptions.alert_last_cherry_price is None and wetmill_data.get('cherry_price_rec', None):
            actual = wetmill_data.get('cherry_price_last', None)
            limit_price = wetmill_data['cherry_price_rec'] * (assumptions.alert_last_cherry_price / Decimal("100"))

            if actual is not None and actual > limit_price:
                wetmill_data['last_cherry_price_alert'] = 'performance-alert'

        wetmill_data['average_cherry_price_alert'] = None
        if not assumptions.alert_average_cherry_price is None and wetmill_data.get('cherry_price_rec', None):
            actual = wetmill_data.get('cherry_price_ytd', None)
            limit_price = wetmill_data['cherry_price_rec'] * (assumptions.alert_average_cherry_price / Decimal("100"))

            if actual is not None and actual > limit_price:
                wetmill_data['average_cherry_price_alert'] = 'performance-alert'

        wetmill_data['working_capital_op_exp_alert'] = None
        if not assumptions.alert_working_capital_op_exp is None:
            actual = wetmill_data.get('working_capital_op_exp', None)

            if actual is not None and actual > assumptions.alert_working_capital_op_exp:
                wetmill_data['working_capital_op_exp_alert'] = 'performance-alert'

        wetmill_data['cash_balance_alert'] = None
        if not assumptions.alert_cash_balance is None:
            actual = wetmill_data.get('cash_balance', None)

            if actual is not None and actual < assumptions.alert_cash_balance:
                wetmill_data['cash_balance_alert'] = 'performance-alert'


def calculate_compliance_ytd(season, wetmill_ids, wetmill_data, today):
    # build a set of our wetmill_ids so we know which to calculate for
    wetmill_id_set = set(wetmill_ids)

    # (wetmill=1, report_day__gte=wetmill2.assumptions.season_start) OR (wetmill=2, report_day__gte=wetmill2.assumptions.season_start)
    day_query = Q(pk__lt=0)
    week_query = Q(pk__lt=0)
    for data in wetmill_data:
        if data['wetmill'].id in wetmill_id_set:
            day_query |= Q(wetmill=data['wetmill'], report_day__gte=data['assumptions'].season_start, report_day__lte=data['assumptions'].season_end)
            week_query |= Q(wetmill=data['wetmill'], start_of_week__gte=data['assumptions'].season_start - timedelta(days=7), start_of_week__lte=data['assumptions'].season_end)

    ibitumbwe_submissions = IbitumbweSubmission.objects.filter(Q(season=season, active=True) & day_query).order_by('wetmill').values('wetmill').annotate(Count('wetmill'), Min('report_day'), Max('report_day'))
    twakinze_submissions = TwakinzeSubmission.objects.filter(Q(season=season, active=True) & day_query).values('wetmill').annotate(Count('wetmill'), Max('report_day'))

    amafaranga_submissions = AmafarangaSubmission.objects.filter(Q(season=season, active=True) & week_query).order_by('wetmill').values('wetmill').annotate(Count('wetmill'), Max('start_of_week'))
    sitoki_submissions =  SitokiSubmission.objects.filter(Q(season=season, active=True) & week_query).order_by('wetmill').values('wetmill').annotate(Count('wetmill'), Max('start_of_week'))


    sub_data = dict()
    for wetmill_id in wetmill_ids:
        sub_data[wetmill_id] = dict()

    for sub in ibitumbwe_submissions:
        sub_data[sub['wetmill']]['ibitumbwe_count_ytd'] = sub['wetmill__count']
        sub_data[sub['wetmill']]['ibitumbwe_date_last'] = sub['report_day__max']

    for sub in twakinze_submissions:
        sub_data[sub['wetmill']]['twakinze_count_ytd'] = sub['wetmill__count']
        sub_data[sub['wetmill']]['twakinze_date_last'] = sub['report_day__max']

    for sub in amafaranga_submissions:
        sub_data[sub['wetmill']]['amafaranga_count_ytd'] = sub['wetmill__count']
        sub_data[sub['wetmill']]['amafaranga_date_last'] = sub['start_of_week__max']

    for sub in sitoki_submissions:
        sub_data[sub['wetmill']]['sitoki_count_ytd'] = sub['wetmill__count']
        sub_data[sub['wetmill']]['sitoki_date_last'] = sub['start_of_week__max']

    for data in wetmill_data:
        wetmill_id = data['wetmill'].id
        data.update(sub_data[wetmill_id])

    ideal_week = (get_week_start_before(datetime.today())).date()
    ideal_yesterday = (datetime.today() - timedelta(days=2)).date()
    today = datetime.today().date()

    # for each wetmill calculate our total submission count and our ideal submission count
    for data in wetmill_data:
        assumptions = data['assumptions']
        data['season_week_start'] = get_week_start_during(min(assumptions.season_start, data.get('cherry_date_first', assumptions.season_start)))
        data['season_day_start'] = min(assumptions.season_start, data.get('cherry_date_first', assumptions.season_start))
        data['season_ideal_last_daily'] = min(today - timedelta(days=1), assumptions.season_end)
        data['season_ideal_last_weekly'] = get_week_start_during(data['season_ideal_last_daily'])

        submission_count = data.get('ibitumbwe_count_ytd', 0) + data.get('amafaranga_count_ytd', 0) + data.get('sitoki_count_ytd', 0) + data.get('twakinze_count_ytd', 0)
        ideal_submission_count = calculate_ideal_submission_count(season, data['wetmill'], data['season_day_start'], data['season_ideal_last_daily'])
        submission_pct = Decimal(submission_count) * Decimal(100) / ideal_submission_count if ideal_submission_count > 0 else None

        data['submission_count'] = submission_count
        data['ideal_submission_count'] = ideal_submission_count
        data['missing_count'] = ideal_submission_count - submission_count
        data['submission_pct'] = submission_pct
        data['season_start'] = assumptions.season_start
        data['season_end'] = assumptions.season_end

        data['daily_current'] = True
        data['sitoki_current'] = True
        data['amafaranga_current'] = True

        if assumptions.season_start <= today <= assumptions.season_end:
            data['daily_current'] = True
            if 'twakinze_date_last' in data or 'ibitumbwe_date_last' in data:
                data['daily_current'] = data.get('twakinze_date_last', ideal_yesterday) > ideal_yesterday or \
                data.get('ibitumbwe_date_last', ideal_yesterday) > ideal_yesterday

            data['sitoki_current'] = data.get('sitoki_date_last', ideal_week) >= ideal_week
            data['amafaranga_current'] = data.get('amafaranga_date_last', ideal_week) >= ideal_week


def build_compliance_data(season, wetmill_data, wetmills, today, user):
    compliance_fields = []

    compliance_fields.append(dict(slug='submission_count', label=_("Reports Submitted/Total Reports Expected")))
    compliance_fields.append(dict(slug='submission_pct', label=_("Reporting Percentage"), help=_("% of Reports Submitted")))
    compliance_fields.append(dict(slug='advance_variance_pct', label=_("% Cherry Advance Variance"), help=_("Variance cherry Advance Reported in Daily Cherry Messages vs. Weekly Cash Messages\nVariance should be 0")))

    if season.country.country_code != 'GT':
        compliance_fields.append(dict(slug='balance_variance_pct', label=_("% Opening Balance Variance"), help=_("Variance opening balance reported this week vs. closing balance calculated last week\nVariance should be 0")))

    wetmill_ids = [w.id for w in wetmills]
    calculate_compliance_ytd(season, wetmill_ids, wetmill_data, today)
    calculate_finance_variance(season, wetmill_ids, wetmill_data, today)

    return compliance_fields, wetmill_data

def build_wetmill_data(season, wetmills, user):
    stock_data = []
    wetmill_ids = [w.pk for w in wetmills]

    cherry_last = calculate_cherry_last(season, wetmill_ids)
    cherry_ytd = calculate_cherry_ytd(season, wetmill_ids)
    sitoki_last = calculate_sitoki_last(season, wetmill_ids)
    parchment_ytd = calculate_parchment_stats(season, wetmill_ids)
    assumptions = load_assumptions_for_wetmills(season, wetmills, user)

    for wetmill in wetmills:
        wetmill_data = dict(wetmill=wetmill, assumptions=assumptions.get(wetmill.id))

        cherry = cherry_last.get(wetmill.pk)
        if cherry:
            wetmill_data.update(cherry)

        cherry = cherry_ytd.get(wetmill.pk)
        if cherry:
            wetmill_data.update(cherry)

        parchment = parchment_ytd.get(wetmill.pk)
        if parchment:
            wetmill_data.update(parchment)

        sitoki = sitoki_last.get(wetmill.pk)
        if sitoki:
            wetmill_data.update(sitoki)

        stock_data.append(wetmill_data)

    calculate_parchment_estimates(stock_data, season.exchange_rate)

    return stock_data

class PredictedOutput(SmartModel):
    """
    Represents the predicted cherry volume going through a volume for the week
    in a season.

    All the values for a season are used in order to build the predicted curve
    of production volume for cherry production
    """
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    week = models.IntegerField(verbose_name=_("Week"))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Percentage"))

    class Meta:
        unique_together = ('season', 'week')
        ordering = ('season', 'week')


class Assumptions(SmartModel):
    """
    Represents the set of assumptions used when calculating aggregated data
    for a particular wet mill.

    These can be modified per season, per wet mill.  
    """
    DEFAULT_FIELDS = ['target', 'cherry_parchment_ratio', 'parchment_green_ratio', 'green_price_differential', 'parchment_value',
                      'washing_station_costs', 'milling_costs', 'working_capital_costs', 'capex_costs', 'fi_costs',
                      'total_wetmill_profit', 'total_farmer_distribution_amount', 'total_yearly_reinvestment_amount',
                      'wetmill_second_price']

    PRICE_FIELDS = ['washing_station_costs', 'milling_costs', 'working_capital_costs', 'capex_costs', 'fi_costs',
                    'total_working_capital', 'total_wetmill_profit', 'total_farmer_distribution_amount',
                    'total_yearly_reinvestment_amount', 'wetmill_second_price']

    ALERT_FIELDS = ['alert_parchment_tabled', 'alert_last_cherry_price', 'alert_average_cherry_price',
                    'alert_working_capital_op_exp', 'alert_cash_balance']

    wetmill = models.ForeignKey(Wetmill, null=True, blank=True, verbose_name=_("Wetmill"),
                                help_text=_("The wetmill these assumptions apply to.  (leave blank for all)"))
    csp = models.ForeignKey(CSP, null=True, blank=True, verbose_name=_("CSP"),
                            help_text=_("The CSP these assumptions apply to."))
    season = models.ForeignKey(Season, verbose_name=_("Season"),
                               help_text=_("The season these assumptions apply to"))

    target = models.IntegerField(null=True, blank=True, verbose_name=_("Target"),
                                 help_text=_("The target cherry to be collected for the wetmill"))

    cherry_parchment_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                                 verbose_name=_("Cherry Parchment Ratio"),
                                                 help_text=_("The estimated cherry/parchment ratio for this wetmill"))
    parchment_green_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                                verbose_name=_("Parchment Green Ratio"),
                                                help_text=_("The estimated parchment/green ratio for this wetmill"))
    green_price_differential = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                                   verbose_name=_("Green Price Differential"),
                                                   help_text=_("The price differential compared to the NY index in USD/Kg Green"))
    parchment_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          verbose_name=_("Parchment Value"),
                                          help_text=_("The estimated value of parchment per kilo in the local currency"))

    washing_station_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                verbose_name=_("Washing Station Costs"),
                                                help_text=_("The washing station costs per kilo of green in USD"))
    milling_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name=_("Milling Costs"),
                                        help_text=_("The milling costs per kilo of green in USD"))
    working_capital_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                verbose_name=_("Working Capital Costs"),
                                                help_text=_("The working capital costs per kilo of green in USD"))
    capex_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      verbose_name=_("Capex Costs"),
                                      help_text=_("The capex costs per kilo of green in USD"))
    fi_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                   verbose_name="F&I Costs",
                                   help_text=_("The F&I costs per kilo of green in USD"))

    total_working_capital = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                                verbose_name=_("Total working capital"),
                                                help_text=_("The total working capital available to the cooperative"))

    total_wetmill_profit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                               verbose_name=_("Total Wetmill Profit"),
                                               help_text=_("The total wetmill profit to be entered at the close of a season"))

    total_farmer_distribution_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                                           verbose_name=_("Total Farmer Distribution Amount"),
                                                           help_text=_("The total farmer distribution amount to be entered at the close of a season"))

    total_yearly_reinvestment_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                                           verbose_name=_("Total Yearly Reinvestment Amount"),
                                                           help_text=_("The total yearly reinvestment amount to be entered at the close of a season"))

    wetmill_second_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                               verbose_name=_("Wetmill Second Price"),
                                               help_text=_("the wetmill's second price entered at the close of a season"))

    season_start = models.DateField(verbose_name=_("Season Start"), help_text=_("When the harvest is predicted to begin"))
    season_end = models.DateField(verbose_name=_("Season End"), help_text=_("When the harvest is predicted to end"))

    alert_parchment_tabled = models.IntegerField(verbose_name=_("High Parchment Tabled Alert"),
                                                 help_text=_("Absolute amount of tabled parchment in kilos above which an alert will be triggered. (leave blank for no alert)"),
                                                 null=True, blank=True)

    alert_last_cherry_price = models.IntegerField(verbose_name=_("Last Cherry Price Alert"),
                                                  help_text=_("Percentage of the recommended price above which an alert should be triggered. (leave blank for no alert)"),
                                                  null=True, blank=True)

    alert_average_cherry_price = models.IntegerField(verbose_name=_("Average Cherry Price Alert"),
                                                     help_text=_("Percentage of the recommended price above which an alert should be triggered. (leave blank for no alert)"),
                                                     null=True, blank=True)

    alert_working_capital_op_exp = models.IntegerField(verbose_name=_("Working Capital Operating Expense Alert"),
                                                       help_text=_("Percentage of uncollateralized working capital above which an alert should be triggered. (leave blank for none)"),
                                                       null=True, blank=True)
    alert_cash_balance = models.IntegerField(verbose_name=_("Cash Balance Alert"),
                                             help_text=_("Absolute value in local currency below which there should be an alert for the cash balance. (leave blank for none)"),
                                             null=True, blank=True)

    def set_defaults(self, default_assumptions):
        """
        Sets default values for our assumptions, these are used if a field is None
        """
        self.defaults = default_assumptions

    def __getattribute__(self, name):

        if hasattr(self, 'defaults') and name in Assumptions.DEFAULT_FIELDS:
            # get our value normally
            value = super(Assumptions, self).__getattribute__(name)

            # if it is not set, use our default's value
            if value is None:
                value = getattr(self.defaults, name)

            return value
        else:
            return super(Assumptions, self).__getattribute__(name)

    @classmethod
    def for_wetmill(cls, season, wetmill, user):
        """
        Returns the Assumptions object that should be used for the passed in wetmill.  This will
        use Season or CSP defaults if no specific Assumptions object is found for the specified
        wetmill.  This function will always return an object.
        """
        # does one exist for this specific wetmill
        assumptions = Assumptions.objects.filter(season=season, wetmill=wetmill)

        # if not, load from the csp
        csp = wetmill.get_csp_for_season(season)

        return Assumptions.for_csp(season, csp, user)


    @classmethod
    def for_csp(cls, season, csp, user):
        assumptions = Assumptions.objects.filter(season=season, csp=csp)

        # if not, try the season
        if not assumptions:
            assumptions = Assumptions.objects.filter(season=season)

        # if we found it, return one
        if assumptions:
            return assumptions[0]

        # otherwise we don't have any even for the season, create some default ones
        return Assumptions.get_or_create(season, None, None, user)

    @classmethod
    def can_edit(cls, season, csp, wetmill, user):
        """
        Returns whether this user can edit these assumptions.
        """
        # we are a country administrator or higher, we can edit
        if user.has_perm('dashboard.assumptions_dashboard'):
            return True

        # if we can edit any sms for this country, we can edit these assumptions
        if user.has_perm('locales.country_sms_edit', season.country):
            return True

        if not csp and wetmill:
            csp = wetmill.get_csp_for_season(season)

        # if we can edit any sms for this csp, we can edit these assumptions
        if csp:
            if user.has_perm('csps.csp_sms_edit', csp):
                return True

        # finally, if we have a wetmill and we can edit those sms, then we can do so
        if wetmill:
            if user.has_perm('wetmills.wetmill_sms_edit', wetmill):
                return True

        return False

    @classmethod
    def get_editable_assumptions_for_season(cls, season, user):
        if user.is_anonymous():
            return None

        # can this user edit season wide?
        if Assumptions.can_edit(season, None, None, user):
            return Assumptions.get_or_create(season, None, None, user)

        # ok, maybe they can edit a csp?
        csps = get_objects_for_user(user, 'csps.csp_sms_edit')
        if csps:
            return Assumptions.get_or_create(season, csps[0], None, user)

        # otherwise, nope, no general editing for you
        return None

    @classmethod
    def get_or_create(cls, season, csp, wetmill, user):
        """
        This will get or create assumptions for the specific set of season, csp and wetmill.  IE, this will
        return an Assumptions object that is specifically for the passed in combination, creating a new
        object if necessary using defaults from the next higher assumptions object.

        Assumptions cascade down, so Season assumptions are used as defaults for CSP assumptions, which are
        used as defaults for Wetmill assumptions.
        """
        existing = Assumptions.objects.filter(season=season, csp=csp, wetmill=wetmill)
        if existing:
            return existing[0]

        year = datetime.now().date().year

        template = dict(season=season,
                        season_start=date(day=1, month=1, year=year), season_end=date(day=31, month=12, year=year))

        # if we have a wetmill set, look for a csp assumption
        template_assumptions = None
        if wetmill:
            template_assumptions = Assumptions.objects.filter(season=season, csp=csp, wetmill=None)

        # if we have a csp, look for season assumptions
        if csp and not template_assumptions:
            template_assumptions = Assumptions.objects.filter(season=season, csp=None, wetmill=None)

        # still nothing? look for the assumptions on previous years
        if not template_assumptions:
            template_assumptions = Assumptions.objects.filter(season__country=season.country, csp=None, wetmill=None).order_by('-season__name')

        if template_assumptions:
            ta = template_assumptions[0]
            template['season_start'] = ta.season_start
            template['season_end'] = ta.season_end

            template['alert_parchment_tabled'] = ta.alert_parchment_tabled
            template['alert_last_cherry_price'] = ta.alert_last_cherry_price
            template['alert_average_cherry_price'] = ta.alert_average_cherry_price
            template['alert_working_capital_op_exp'] = ta.alert_working_capital_op_exp
            template['alert_cash_balance'] = ta.alert_cash_balance

            if wetmill:
                template['wetmill'] = wetmill
            elif csp:
                template['csp'] = csp

        # if we are creating new season assumptions, initialize the recommended price variables with some defaults
        if csp is None and wetmill is None:
            template['target'] = 150000
            template['cherry_parchment_ratio'] = Decimal("5.2")
            template['parchment_green_ratio'] = Decimal("2.5")
            template['green_price_differential'] = Decimal("0")
            template['parchment_value'] = Decimal("220")
            template['washing_station_costs'] = Decimal("0.74")
            template['milling_costs'] = Decimal("0.40")
            template['working_capital_costs'] = Decimal("0.18")
            template['capex_costs'] = Decimal("0.16")
            template['fi_costs'] = Decimal("0.16")

            template['alert_last_cherry_price'] = Decimal("100")
            template['alert_average_cherry_price'] = Decimal("100")
            template['alert_working_capital_op_exp'] = Decimal("35")
            template['alert_cash_balance'] = Decimal("0")

        template['created_by'] = user
        template['modified_by'] = user

        assumptions = Assumptions.objects.create(**template)

        return assumptions

    class Meta:
        unique_together = (('season', 'wetmill'), ('season', 'csp'))

def remove_current_datapoint(context, actual_key):
    """
    If our data set's last point isn't for a week that has completed yet, remove that point
    and return a new dataset that contains it.  Otherwise, return an empty dataset.
    """
    current = []

    dataset = context[actual_key]
    if dataset:
        last_point = dataset[-1]

        # is this last point in the future?
        last_day = datetime.fromtimestamp(last_point[0] / 1000)
        today = datetime.now().today()

        if last_day + timedelta(days=7) > today:
            # create a new dataset of just this item
            current.append([int(today.strftime("%s")) * 1000, last_point[1]])
            del dataset[-1]

    return current

def calculate_projected_cherry(day, length, total, outputs):
    """
    Returns the total amount of cherry collected by this day
    """
    # if the current day is past our season's predicted length, then projected is just our total
    if day >= length:
        return total

    # negative day
    if day < 0:
        return 0

    # what percentage are they through the real season (as float)
    percentage = day / (length * 1.0)

    # figure out what week this lands on in our ideal world
    ideal_length = len(outputs) * 7
    ideal_day = percentage * ideal_length
    ideal_week = int(ideal_day / 7)

    # calculate our total percentage
    harvested = sum([float(o.percentage) for o in outputs[:ideal_week]])
    if ideal_day > 0:
        harvested += float(outputs[ideal_week].percentage) * ((ideal_day % 7) / 7)

    # this now the total harvested up to this day
    return harvested * total / 100.0

def as_percent(numerator, denominator):
    if denominator and denominator > Decimal(0):
        return ((numerator * Decimal('100')) / denominator).quantize(Decimal("0.0"))
    else:
        return None

def calculate_price_chart(season, wetmill_data):
    daily_cherry = IbitumbweSubmission.objects.filter(season=season, wetmill__in=[wetmill_data['wetmill']]).order_by('report_day').values('report_day').annotate(Sum('cherry_purchased'), Sum('cash_spent'), Sum('credit_spent'))

    prices = []

    for day in daily_cherry:
        summary = dict()
        summary['day'] = int(day['report_day'].strftime("%s")) * 1000

        cherry = day['cherry_purchased__sum']
        paid = day['cash_spent__sum'] + day['credit_spent__sum']

        if cherry > Decimal(0):
            summary['price'] = (paid / cherry + Decimal(".5")).quantize(Decimal("1"))
            summary['cherry'] = cherry
            prices.append(summary)

    nyc_prices = []

    if not daily_cherry:
        return (prices, nyc_prices)

    current = daily_cherry[0]['report_day']
    last = daily_cherry[len(daily_cherry)-1]['report_day']

    raw_prices = list(NYCherryPrice.objects.filter(date__gte=current, date__lte=last))
    raw_prices_i = 0

    season_assumptions = Assumptions.objects.get(season=season, csp=None, wetmill=None)

    csp = wetmill_data['wetmill'].get_csp_for_season(season)
    csp_assumptions = Assumptions.for_csp(season, csp, None)

    washing_station_costs = get_attr(csp_assumptions, 'washing_stations_costs', get_attr(season_assumptions, 'washing_station_costs', Decimal("0.74")))
    milling_costs = get_attr(csp_assumptions, 'milling', get_attr(season_assumptions, 'milling_costs', Decimal("0.40")))
    working_capital_costs = get_attr(csp_assumptions, 'working_capital_costs', get_attr(season_assumptions, 'working_capital_costs', Decimal("0.16")))
    capex_costs = get_attr(csp_assumptions, 'capex_costs', get_attr(season_assumptions, 'capex_costs', Decimal("0.18")))
    fi_costs = get_attr(csp_assumptions, 'fi_costs', get_attr(season_assumptions, 'fi_costs', Decimal("0.16")))

    assumptions = wetmill_data['assumptions']
    production_costs = get_attr(assumptions, 'washing_station_costs', washing_station_costs) + \
                       get_attr(assumptions, 'milling_costs', milling_costs) + \
                       get_attr(assumptions, 'working_capital_costs', working_capital_costs) + \
                       get_attr(assumptions, 'capex_costs', capex_costs) + \
                       get_attr(assumptions, 'fi_costs', fi_costs)

    cherry_green_ratio = assumptions.cherry_parchment_ratio * assumptions.parchment_green_ratio

    while current <= last:
        while raw_prices_i < len(raw_prices) and raw_prices[raw_prices_i].date < current:
            raw_prices_i += 1

        if raw_prices_i < len(raw_prices) and raw_prices[raw_prices_i].date == current:
            # do we have a NYC price for this day?
            nyc_price = raw_prices[raw_prices_i].calculate_recommended_price(assumptions.green_price_differential,
                                                                             production_costs,
                                                                             cherry_green_ratio,
                                                                             season.exchange_rate)
            nyc_prices.append(dict(day=int(current.strftime("%s")) * 1000, price=nyc_price))

        current = current + timedelta(days=1)

    return (prices, nyc_prices)

def calculate_cp_chart(season, wetmill):
    from reports.models import Report
    from aggregates.models import ReportValue, SeasonAggregate

    years = []

    # look for previous reports
    report_collection = Report.objects.filter(wetmill=wetmill, season__is_finalized=True).order_by('season__name')
    # We are not using the simple array slice operation here because of a bug in this version of django that prevents it from supporting
    # negative indexes.  Once upraded, we will switch this to [:-3]
    if len(report_collection) >= 3:
        report_collection = report_collection[len(report_collection)-3:]

    for report in report_collection:
        report_season = report.season
        year = dict(name=report_season.name)

        season_average = SeasonAggregate.objects.filter(season=report_season, slug='cherry_to_parchment_ratio')
        if season_average:
            year['average'] = season_average[0].average.quantize(Decimal(".01"))
        else:
            year['average'] = Decimal(0)

        wetmill_cp_ratio = ReportValue.objects.filter(report__season=report_season, report__wetmill=wetmill, metric__slug='cherry_to_parchment_ratio')
        if wetmill_cp_ratio:
            year['wetmill'] = wetmill_cp_ratio[0].value.quantize(Decimal(".01"))
        else:
            year['wetmill'] = Decimal(0)

        years.append(year)

    # add the current season using SMS data if it isn't finalized
    # (The following code segment was commented out and that had
    # been causing new wetmills with no history in the system to show empty for the Cherry:Parchment Ratio)
    # The reason for the commenting of the code was not written down.  Therefore it should be watched carefully

    if not season.is_finalized:
        year = dict(name=season.name)
        year['average'] = calculate_cp_ratio(season, Wetmill.objects.filter(country=season.country))
        year['wetmill'] = calculate_cp_ratio(season, Wetmill.objects.filter(pk=wetmill.pk))
        years.append(year)

    return years

def calculate_expenses_chart(season, wetmills):
    expenses = AmafarangaSubmission.objects.filter(season=season, wetmill__in=[w['wetmill'] for w in wetmills]).values('season').annotate(\
        Sum('working_capital'), Sum('other_income'), Sum('advanced'), Sum('full_time_labor'),
        Sum('casual_labor'), Sum('commission'), Sum('transport'), Sum('other_expenses'))

    expense_data = dict(advanced=0, labor=0, transport=0, other=0)

    if expenses:
        expenses = expenses[0]

        advanced = expenses['advanced__sum']
        labor = expenses['casual_labor__sum'] + expenses['full_time_labor__sum']
        transport = expenses['transport__sum']
        other = expenses['commission__sum'] + expenses['other_expenses__sum']

        total = advanced + labor + transport + other

        expense_data['advanced'] = as_percent(advanced, total)
        expense_data['labor'] = as_percent(labor, total)
        expense_data['transport'] = as_percent(transport, total)
        expense_data['other'] = as_percent(other, total)

    return expense_data

def calculate_cp_ratio(season, wetmills):
    # when was the last report in theory?
    last_weekly_report = get_week_start_before(datetime.now())
    last_cherry = last_weekly_report - timedelta(days=5)

    cherry = IbitumbweSubmission.objects.filter(season=season, wetmill__in=wetmills, report_day__lte=last_cherry).\
                                                values('season').annotate(Sum('cherry_purchased'))
    parchment = SitokiSubmission.objects.filter(season=season, wetmill__in=wetmills).\
                                                values('season').annotate(Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'))

    cp_ratio = Decimal(0)

    if cherry and parchment:
        parchment = parchment[0]
        cherry = cherry[0]

        total_parchment = parchment['grade_a_stored__sum'] + parchment['grade_b_stored__sum'] + parchment['grade_c_stored__sum']
        total_cherry = cherry['cherry_purchased__sum']

        if total_parchment:
            cp_ratio = (total_cherry / total_parchment).quantize(Decimal(".01"))

    return cp_ratio

def calculate_actual_cherry_curve(season, wetmills):
    daily_cherry = IbitumbweSubmission.objects.filter(season=season, wetmill__in=[w['wetmill'] for w in wetmills]).order_by('report_day').values('report_day').annotate(Sum('cherry_purchased'))

    # ok, now we need to roll these up by week, starting on Fridays
    weekly_cherry = []
    week_total = 0
    week_start = None

    for day in daily_cherry:
        report_day = day['report_day']
        report_week = get_week_start_during(report_day)

        # no week yet, set our week start
        if not week_start:
            week_start = report_week

        # this is for a new week, save away our current totals
        elif week_start != report_week:
            while week_start < report_week:
                weekly_cherry.append([int(week_start.strftime("%s")) * 1000, week_total])
                week_start = week_start + timedelta(days=7)
                week_total = 0

        week_total += day['cherry_purchased__sum']

    if week_start:
        weekly_cherry.append([int(week_start.strftime("%s")) * 1000, week_total])

    return weekly_cherry

def convert_weekly_to_total(weekly_values):
    total = 0
    weekly_total = []

    for week in weekly_values:
        total += week[1]
        weekly_total.append([week[0], total])

    return weekly_total

def calculate_projected_cherry_on_day(day, length, total, outputs):
    """
    Calculates the projected cherry volume given the following variables:
        day: what day in the wet mill's season this is (since it started)
        length: the total length in days of the wet mill's season
        total: the total output projected for this wet mill
        outputs: our list of projected output percentages, per week
    """
    # if the current day is past our season's predicted length, then projected is just our total
    if day >= length:
        return 0

    # negative day
    if day < 0:
        return 0

    today_total = calculate_projected_cherry(day, length, total, outputs)
    tomorrow_total = calculate_projected_cherry(day + 1, length, total, outputs)

    return tomorrow_total - today_total

def adjust_currency_per_weight_values(weight, wetmill_data):
    per_weight_fields = ('cherry_price_ytd', 'cherry_price_last', 'cherry_price_rec')

    for wetmill in wetmill_data:
        for field in per_weight_fields:
            value = wetmill.get(field, None)
            if value:
                wetmill[field] = value * weight.ratio_to_kilogram

def convert_to_usd(season, wetmill_data):
    currency_fields = ('cherry_price_ytd', 'cherry_price_last', 'cherry_price_rec', 'cherry_spent_last', 'cherry_spent_ytd', 'production_costs',
                       'working_capital_ytd', 'working_capital_unc', 'cash_balance', 'parchment_value', 'capex_ytd', 'op_exp_ytd', 'total_exp_ytd',
                       'est_total_parchment_value')

    for wetmill in wetmill_data:
        for field in currency_fields:
            value = wetmill.get(field, None)
            if value:
                wetmill[field] = value / season.exchange_rate

    for wetmill in wetmill_data:
        if wetmill['assumptions'].total_working_capital:
            wetmill['assumptions'].total_working_capital = wetmill['assumptions'].total_working_capital / season.exchange_rate

def calculate_totals(stock_fields, stock_data):
    totals = dict()

    for field in stock_fields:
        slug = field['slug']

        if slug == 'cherry_ytd':
            total = sum([s.get('cherry_ytd', Decimal(0)) for s in stock_data])
            totals['cherry_tons_ytd'] = Decimal(total).quantize(Decimal(".1"))

        if slug == 'cherry_price_last':
            total_spent = sum([s.get('cherry_price_last', Decimal(0)) * s.get('cherry_last', Decimal(0)) for s in stock_data])
            total_kilos = sum([s.get('cherry_last', Decimal(0)) for s in stock_data])

            total = None
            if total_kilos > 0:
                total = total_spent / total_kilos

        elif slug == 'cherry_price_ytd':
            total_kilos = 0
            try:
                total_spent = sum([s.get('cherry_price_ytd', Decimal(0)) * s.get('cherry_ytd', Decimal(0)) for s in stock_data])
                total_kilos = sum([s.get('cherry_ytd', Decimal(0)) for s in stock_data])
            except TypeError:
                pass

            total = None
            if total_kilos > 0:
                total = total_spent / total_kilos

            # Calculate the Estimated Value of Parchment
            est_stored_parchment_value = sum([s.get('est_stored_parchment_value', Decimal(0)) for s in stock_data])
            est_total_parchment_value = sum([s.get('est_total_parchment_value', Decimal(0)) for s in stock_data])
            totals['est_stored_parchment_value'] = est_stored_parchment_value
            totals['est_total_parchment_value'] = est_total_parchment_value

        elif slug == 'cherry_price_rec':
            total_price = sum([s.get('cherry_price_rec', Decimal(0)) for s in stock_data])
            total_count = len(stock_data)

            total = None
            if total_count > 0:
                total = total_price / total_count

        elif slug == 'working_capital_op_exp':
            total_working_capital = sum([s.get('working_capital_ytd', Decimal(0)) for s in stock_data])
            total_op_exp = sum([s.get('op_exp_ytd', Decimal(0)) for s in stock_data])
            total_exp = sum([s.get('total_exp_ytd', Decimal(0)) for s in stock_data])

            working_capital_million_ytd = Decimal(0)
            if total_working_capital:
                totals['working_capital_ytd'] = total_working_capital
                working_capital_million_ytd = (total_working_capital / Decimal("1000000")).quantize(Decimal(".001"))

            totals['working_capital_million_ytd'] = working_capital_million_ytd

            total = None
            if total_working_capital > 0 and total_exp > 0:
                total = total_op_exp * Decimal(100) / total_exp

            total_working_capital_available = sum([s['assumptions'].total_working_capital or Decimal(0) for s in stock_data])

            if total_working_capital_available > Decimal(0):
                working_capital_received_percent = (total_working_capital / total_working_capital_available) * Decimal("100")
                totals['working_capital_received_percent'] = working_capital_received_percent

            total_est_total_parchment_value = sum([s.get('est_total_parchment_value', Decimal(0)) for s in stock_data])
            if total_working_capital > Decimal(0):
                est_profitability_ytd = (total_est_total_parchment_value/total_working_capital - 1) * Decimal("100")
                totals['est_profitability_ytd'] = est_profitability_ytd

        elif slug == 'submission_pct':
            total_actual = sum([s.get('submission_count', Decimal(0)) for s in stock_data])
            total_ideal = sum([s.get('ideal_submission_count', Decimal(0)) for s in stock_data])
            total_missing = sum([s.get('missing_count', Decimal(0)) for s in stock_data])

            totals['ideal_submission_count'] = total_ideal
            totals['missing_count'] = total_missing

            if total_ideal > 0:
                total = total_actual * Decimal(100) / total_ideal
            else:
                total = None

        elif slug == 'parchment_stored_ytd':
            total = sum([s.get('parchment_stored_ytd', Decimal(0)) for s in stock_data])
            totals['parchment_tons_stored_ytd'] = Decimal(total).quantize(Decimal(".1"))

        elif slug == 'parchment_in_store':
            total = sum([s.get('parchment_in_store', Decimal(0)) for s in stock_data])
            totals['parchment_in_store'] = Decimal(total).quantize(Decimal(".1"))

            # Calculate Percent Of Parchment Shipped
            total_stored = sum([s.get('parchment_stored_ytd', Decimal(0)) for s in stock_data])
            total_shipped = sum([s.get('parchment_shipped_ytd', Decimal(0)) for s in stock_data])
            if total_stored > Decimal(0):
                percent_of_parchment_shipped = total_shipped * Decimal("100") / Decimal(total_stored)
                totals['percent_of_parchment_shipped'] = percent_of_parchment_shipped

        else:
            total = sum([s.get(slug, Decimal(0)) for s in stock_data])

        totals[slug] = total

    return totals

def calculate_predicted_cherry_curve(season, wetmills):
    # we are going to store the curve as an array of pairs with date, value pairs
    curve = []

    # load our predicted outputs for this season
    outputs = PredictedOutput.objects.filter(season=season).order_by('week')

    # for each wetmill
    for wetmill_data in wetmills:
        assumptions = wetmill_data['assumptions']
        season_start = get_week_start_during(wetmill_data.get('cherry_date_first', assumptions.season_start))
        season_length = (assumptions.season_end - season_start).days

        wm_curve = calculate_wetmill_predicted_cherry_curve(season_start,
                                                            season_length,
                                                            assumptions.target,
                                                            outputs)

        # merge our curve with our global curve
        if not curve:
            curve = wm_curve
        else:
            index = 0
            wm_index = 0

            # merge our wetmill curve with our global one
            while wm_index < len(wm_curve) and index < len(curve):
                wm_timestamp = wm_curve[wm_index][0]
                timestamp = curve[index][0]

                # the first date is before our current curve
                if wm_timestamp < timestamp:
                    # insert this pair in our array
                    curve.insert(index, wm_curve[wm_index])
                    wm_index += 1
                    index += 1

                # date are the same, need to sum them
                elif wm_timestamp == timestamp:
                    curve[index] = (timestamp, curve[index][1] + wm_curve[wm_index][1])
                    wm_index += 1
                    index += 1

                # the date comes after the current curve, increment it
                else:
                    index += 1

            # still have unprocessed items, append them
            while wm_index < len(wm_curve):
                curve.append(wm_curve[wm_index])
                wm_index += 1

    return curve


def calculate_wetmill_predicted_cherry_curve(start, length, total, outputs):
    """
    Calculates a full cherry production curve.
         total: the total output projected for this wet mill
         outputs: our list of projected output percentages, per week for the ideal season
    """
    current = datetime(start.year, start.month, start.day, 0, 0, 0, 0, pytz.utc)

    day = 0
    week_total = 0

    cherry = []

    # now for each day, calculate the predicted value for that day
    while day <= length:
        # this is a full week?
        if day % 7 == 0:
            # append our week's haul
            cherry.append((int(time.mktime(current.timetuple())) * 1000, week_total))
            current = current + timedelta(days=7)
            week_total = 0

        day_cherry = calculate_projected_cherry_on_day(day, length, total, outputs)
        week_total += day_cherry
        day += 1

    # extra day to add?
    if (day - 1) % 7 != 0:
        cherry.append((int(time.mktime(current.timetuple())) * 1000, week_total))
        current = current + timedelta(days=7)

    # add a last 0
    cherry.append((int(time.mktime(current.timetuple())) * 1000, 0))

    return cherry


def calculate_estimated_stored_parchment_value_curve(season, wetmill, user):

    assumptions = load_assumptions_for_wetmills(season, [wetmill, ], user)
    assumptions = assumptions.get(wetmill.id)
    season_start = assumptions.season_start
    season_length = (assumptions.season_end - season_start).days

    start = season_start
    length = season_length

    current = datetime(start.year, start.month, start.day, 0, 0, 0, 0, pytz.utc)

    day = 0
    week_total = 0

    parchment_est = []

    while day <= length and (current.date() <= datetime.now().date() and current.date() <= assumptions.season_end):
        # now for each day, calculate the predicted value for that day
        while day <= length and (current.date() <= datetime.now().date() and current.date() <= assumptions.season_end):
            # this is a full week?
            if day % 7 == 0:
                est_stored_parchment_this_week = calculate_weekly_wetmill_data(season=season, wetmill=wetmill, user=user, until_date=current)
                if est_stored_parchment_this_week[0].get('est_stored_parchment_value'):
                    parchment_est.append((int(time.mktime(current.timetuple())) * 1000, est_stored_parchment_this_week[0]['est_stored_parchment_value']))
                current = current + timedelta(days=7)

            day += 1

        # extra day to add?
        if (day - 1) % 7 != 0:
            est_stored_parchment_this_week = calculate_weekly_wetmill_data(season=season, wetmill=wetmill, user=user, until_date=current)
            if est_stored_parchment_this_week[0].get('est_stored_parchment_value'):
                parchment_est.append((int(time.mktime(current.timetuple())) * 1000, est_stored_parchment_this_week[0]['est_stored_parchment_value']))
            current = current + timedelta(days=7)

        wm_curve = []

        wm_curve = parchment_est

        return wm_curve


def calculate_weekly_wetmill_data(season, wetmill, user, until_date):
    stock_data = []
    wetmill_id = wetmill.pk

    cherry_ytd = calculate_cherry_ytd(season, wetmill_id, until_date)
    parchment_ytd = calculate_parchment_stats(season, wetmill_id, until_date)
    assumptions = load_assumptions_for_wetmills(season, [wetmill, ], user)

    wetmill_data = dict(wetmill=wetmill, assumptions=assumptions.get(wetmill.id))

    cherry = cherry_ytd.get(wetmill.pk)
    if cherry:
        wetmill_data.update(cherry)

    parchment = parchment_ytd.get(wetmill.pk)
    if parchment:
        wetmill_data.update(parchment)

    stock_data.append(wetmill_data)

    calculate_parchment_estimates(stock_data, season.exchange_rate)

    return stock_data


def calculate_estimated_total_parchment_value_curve(season, wetmill, user):
    assumptions = load_assumptions_for_wetmills(season, [wetmill, ], user)
    assumptions = assumptions.get(wetmill.id)
    season_start = assumptions.season_start
    season_length = (assumptions.season_end - season_start).days

    start = season_start
    length = season_length

    current = datetime(start.year, start.month, start.day, 0, 0, 0, 0, pytz.utc)

    day = 0

    parchment_est = []

    # now for each day, calculate the predicted value for that day
    while day <= length and (current.date() <= datetime.now().date() and current.date() <= assumptions.season_end):
        # this is a full week?

        # append our week's haul
        est_total_parchment_this_week = calculate_weekly_wetmill_data(season=season, wetmill=wetmill, user=user, until_date=current)
        if est_total_parchment_this_week[0].get('est_total_parchment_value'):
            parchment_est.append((int(time.mktime(current.timetuple())) * 1000, est_total_parchment_this_week [0]['est_total_parchment_value']))
        current = current + timedelta(days=7)

        day += 1

    # extra day to add?
    if (day - 1) % 7 != 0:
        est_total_parchment_this_week = calculate_weekly_wetmill_data(season=season, wetmill=wetmill, user=user, until_date=current)
        if est_total_parchment_this_week[0].get('est_total_parchment_value'):
            parchment_est.append((int(time.mktime(current.timetuple())) * 1000, est_total_parchment_this_week [0]['est_total_parchment_value']))
        current = current + timedelta(days=7)

    wm_curve = []

    wm_curve = parchment_est

    return wm_curve


def calculate_working_capital_curve(season, wetmill, user):
    assumptions = load_assumptions_for_wetmills(season, [wetmill, ], user)
    assumptions = assumptions.get(wetmill.id)
    season_start = assumptions.season_start
    season_length = (assumptions.season_end - season_start).days

    start = season_start
    length = season_length

    current = datetime(start.year, start.month, start.day, 0, 0, 0, 0, pytz.utc)

    day = 0

    working_capital = []

    # now for each day, calculate the predicted value for that day
    while day <= length and (current.date() <= datetime.now().date() and current.date() <= assumptions.season_end):
        # this is a full week?
        if day % 7 == 0:
            # append our week's haul
            total_working_capital_this_week = calculate_amafaranga_ytd(season, [wetmill.pk, ], current)
            if total_working_capital_this_week.get(wetmill.pk):
                working_capital.append((int(time.mktime(current.timetuple())) * 1000, total_working_capital_this_week.get(wetmill.pk)['working_capital_ytd']))
            current = current + timedelta(days=7)

        day += 1

    # extra day to add?
    if (day - 1) % 7 != 0:
        total_working_capital_this_week = calculate_amafaranga_ytd(season, [wetmill.pk, ], current)
        if total_working_capital_this_week.get(wetmill.pk):
            working_capital.append((int(time.mktime(current.timetuple())) * 1000, total_working_capital_this_week.get(wetmill.pk)['working_capital_ytd']))
        current = current + timedelta(days=7)

    wm_curve = []

    wm_curve = working_capital

    return wm_curve



class NYCherryPrice(SmartModel):
    date = models.DateField(help_text="The date that this cherry price was looked up")
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                help_text="The price on that day")

    @classmethod
    def update_nyc_price(cls):
        today = datetime.today()
        price = NYCherryPrice.lookup_nyc_price()
        if price:
            anon_user = User.objects.get(pk=-1)
            return NYCherryPrice.objects.create(date=today,
                                                price=price,
                                                created_by=anon_user,
                                                modified_by=anon_user)
        else:
            return None

    @classmethod
    def lookup_nyc_price(cls):
        url = settings.NYC_PRICE_URL
        now = timezone.now()

        if now.month <= 5:
            year = now.year % 100
        else:
            year = (now.year % 100) + 1

        url = url.replace("{{YEAR}}", str(year))

        r = requests.get(url, headers={ 'User-Agent': 'Mozilla/4.0' })

        # ok, let's find our div now
        if r.status_code == 200:
            html = fromstring(r.text)
            sel = CSSSelector(settings.NYC_PRICE_SELECTOR)

            matches = sel(html)
            if matches:
                # remove anything that isn't numeric
                price = Decimal(re.sub('[^0-9\.]', '', matches[0].text))

                # price at this point is in cents and lbs.. we need to convert to dollars / kilo
                price = price * Decimal("2.20462") / Decimal("100")

                return Decimal(price)

        return None

    def calculate_recommended_price(self, price_differential, production_costs, cherry_parchment_ratio, exchange_rate):
        average_fob_price = self.price + price_differential
        profit = average_fob_price - production_costs
        profit_per_kilo = profit / cherry_parchment_ratio

        return profit_per_kilo * exchange_rate


