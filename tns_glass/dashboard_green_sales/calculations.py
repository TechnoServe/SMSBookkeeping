from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.db.models import F

from sms.models import IgurishaSubmission, DepanseSubmission


from wetmills.models import WetmillCSPSeason

PARCHMENT_TO_GREEN_RATIO = Decimal(0.6)

from dashboard_green_sales_charts.views.engine import ChartEngine, TableEngine
from dashboard_green_sales_charts.views.bar import BarChart
from dashboard_green_sales_charts.views.line import LineChart
from dashboard_green_sales_charts.views.column import ColumnChart
from dashboard_green_sales_charts.views.pie import PieChart
from dashboard_green_sales_charts.views.datatable import DataTable
from django.core.urlresolvers import reverse

from dashboard.models import calculate_parchment_stats, load_assumptions_for_wetmills_by_id

## Overall

def total_sales_ytd(season, wetmill_ids, currency, until_date=None, sale_types=None):
    sales = IgurishaSubmission.objects.filter(
        season=season
    )
    if wetmill_ids:
        sales = sales.filter(wetmill__in=wetmill_ids)
    if until_date:
        sales = sales.filter(sales_date__lte=until_date)
    if sale_types:
        sales = sales.filter(sale_type__in=sale_types)

    total_sales = sales.extra(
        select={'total_sales': 'SUM(volume * price * exchange_rate)'}
    ).values('total_sales')[0]['total_sales']
    return total_sales if total_sales else 0


def average_sales_price_ytd(season, wetmill_ids, currency, until_date=None, sale_types=None):
    sales = IgurishaSubmission.objects.filter(
        season=season
    )
    if wetmill_ids:
        sales = sales.filter(wetmill__in=wetmill_ids)
    if until_date:
        sales = sales.filter(sales_date__lte=until_date)
    if sale_types:
        sales = sales.filter(sale_type__in=sale_types)

    sales_price = sales.extra(
        select={'avg_sales_price': 'AVG(price * exchange_rate)'}
    ).values('avg_sales_price')[0]['avg_sales_price']
   
    return sales_price if sales_price else 0


def total_parchment_volume(season, wetmill_ids, currency, until_date=None):
    #Total Parchment Volume = Total Stock
    
    parchment_ytd = calculate_parchment_stats(season, wetmill_ids)

    parchment_sum = 0

    for wetmill_id in wetmill_ids:
        if wetmill_id in parchment_ytd:
            parchment_sum += (parchment_ytd[wetmill_id])['parchment_stored_ytd']
    
    return parchment_sum


def estmated_parchment_vol_remaining(season, wetmill_ids, currency, user, until_date=None):
    assumptions = load_assumptions_for_wetmills_by_id(season, wetmill_ids, user)

    parchment_remaining_sum = 0

    for wetmill_id in wetmill_ids:
        PARCHMENT_TO_GREEN_RATIO = assumptions.get(wetmill_id).parchment_green_ratio
        parchment_stock = total_parchment_volume(season, [wetmill_id], currency, until_date)
        exports_green = total_export_vol_ytd(season, [wetmill_id,], currency, until_date)
        exports_parch = PARCHMENT_TO_GREEN_RATIO * exports_green
        local = total_local_vol_ytd(season, [wetmill_id,], currency, until_date)
        parchments_sold = exports_parch + local
        parchments_remaining = 0
        if parchment_stock < parchments_sold:
            parchments_remaining = 0
        else:
            parchments_remaining = parchment_stock - parchments_sold
        parchment_remaining_sum += parchments_remaining

    return parchment_remaining_sum

def total_parchment_export(season, wetmill_ids, currency, user, until_date=None):
    total = 0
    assumptions = load_assumptions_for_wetmills_by_id(season, wetmill_ids, user)

    for wetmill_id in wetmill_ids: #we have to iterate because the parchment_green_ratio is different for each wetmill.
        PARCHMENT_TO_GREEN_RATIO = assumptions.get(wetmill_id).parchment_green_ratio
        exports_green = total_export_vol_ytd(season, [wetmill_id,], currency, until_date)
        exports_parch = PARCHMENT_TO_GREEN_RATIO * exports_green

        total += exports_parch

    return total

def estimated_percent_sold_ytd(season, wetmill_ids, currency, user, until_date=None):
    total_parchment_stock = total_parchment_volume(season, wetmill_ids, currency, until_date)

    exports_parch = total_parchment_export(season, wetmill_ids,currency, user, until_date)
    local = total_local_vol_ytd(season, wetmill_ids, currency, until_date)

    parchments_sold = exports_parch + local
    if not total_parchment_stock:
        return 0
    return Decimal(parchments_sold) * Decimal("100") / Decimal(total_parchment_stock)


def sales_expenses_ytd(season, wetmill_ids, currency, until_date=None, selected_fields=None):
    if not selected_fields:
        selected_fields = 'milling+marketing+export+finance+capex+govt+other'
    expenses = DepanseSubmission.objects.filter(
        season=season,
        is_active=True
    )
    if wetmill_ids:
        expenses = expenses.filter(wetmill__in=wetmill_ids)
    if until_date:
        expenses = expenses.filter(sales_date__lte=until_date)
    sales_expenses = expenses.extra(
        select={'total_expenses': 'SUM({})'.format(selected_fields)}
    ).values('total_expenses')[0]['total_expenses']
    
    return sales_expenses if sales_expenses else 0


## Export 
# The following figures should then be shown for only the sales with the type 
# FOT or FOB

def total_export_sales_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['FOT', 'FOB']
    return total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )


def average_export_sales_price_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['FOT', 'FOB']
    return average_sales_price_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )


def total_export_vol_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['FOT', 'FOB']
    sales = IgurishaSubmission.objects.filter(
        season=season,
        sale_type__in=sale_types
    )
    if wetmill_ids:
        sales = sales.filter(wetmill__in=wetmill_ids)
    if until_date:
        sales = sales.filter(sales_date__lte=until_date)
    total_volume = sales.aggregate(
        Sum('volume')
    )['volume__sum']
    
    return total_volume if total_volume else 0


def percent_of_total_sales_revenue(season, wetmill_ids, currency, until_date=None):
    sale_types = ['FOT', 'FOB']
    
    _total_export_sales_ytd = total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )
    _total_sales_ytd = total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date
    )
    if not _total_sales_ytd:
        return 0
    return Decimal(_total_export_sales_ytd) * Decimal("100")/Decimal(_total_sales_ytd)


## Local
# The following figures should then be shown for only the sales with the type 
# Local

def total_local_sales_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['L']
    return total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )


def average_local_sales_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['L']
    return average_sales_price_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )


def total_local_vol_ytd(season, wetmill_ids, currency, until_date=None):
    sale_types = ['L']
    sales = IgurishaSubmission.objects.filter(
        season=season,
        sale_type__in=sale_types
    )
    if wetmill_ids:
        sales = sales.filter(wetmill__in=wetmill_ids)
    if until_date:
        sales = sales.filter(sales_date__lte=until_date)
    total_volume = sales.aggregate(
        Sum('volume')
    )['volume__sum']
    
    return total_volume if total_volume else 0


def percent_of_local_sales_vol(season, wetmill_ids, currency, until_date=None):
    sale_types = ['L']
    
    _total_export_sales_ytd = total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date,
        sale_types=sale_types
    )
    _total_sales_ytd = total_sales_ytd(
        season,
        wetmill_ids,
        currency,
        until_date=until_date
    )
    if not _total_sales_ytd: return 0
    return Decimal(_total_export_sales_ytd) * Decimal("100") / Decimal(_total_sales_ytd)


## Table generator

def generate_sales_table(season, selected_wetmills, currency, until_date=None):
    table_columns =  [
        { "title": "Wetmills", "type": "url"},
        { "title": "Export Sales Volume YTD" },
        { "title": "Average Export Sale Price YTD" },
        { "title": "Export Sales Amount YTD" },
        { "title": "Local Sales Volume YTD" },
        { "title": "Average Local Sale Price YD" },
        { "title": "Local Sales Amount YD" },
    ]
    
    dataset = []
    for wetmill in selected_wetmills:
        wetmill_url = reverse('dashboard_green_sales.wetmill_wetmillsales', args=[wetmill.id]) + '?season=' + str(season.id)
        wetmill_link = '[{}]({})'.format(wetmill.name, wetmill_url)
        wetmill_data = [
            wetmill_link,
            total_export_vol_ytd(season, [wetmill.id], currency),
            average_export_sales_price_ytd(season, [wetmill.id], currency),
            total_export_sales_ytd(season, [wetmill.id], currency),
            total_local_vol_ytd(season, [wetmill.id], currency),
            average_local_sales_ytd(season, [wetmill.id], currency),
            total_local_sales_ytd(season, [wetmill.id], currency),
        ]
        dataset.append(wetmill_data)
    table_data = {
        "table_name": "sales_table",
        "dataset": dataset,
        "table_columns": table_columns
    }

    table_engine = TableEngine(**table_data)
    return table_engine.table


def generate_selling_expenses_table(season, selected_wetmills, currency, until_date=None):
    table_columns =  [
        { "title": "Wetmills", "type": "url" },
        { "title": "Milling" },
        { "title": "Marketing" },
        { "title": "Export" },
        { "title": "Finance" },
        { "title": "Capex" },
        { "title": "Govt" },
        { "title": "Other" }
    ]
    
    dataset = []
    
    for wetmill in selected_wetmills:
        wetmill_url = reverse('dashboard_green_sales.wetmill_wetmillsales', args=[wetmill.id]) + '?season=' + str(season.id)
        wetmill_link = '[{}]({})'.format(wetmill.name, wetmill_url)
        wetmill_data = [
            wetmill_link,
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='milling'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='marketing'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='export'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='finance'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='capex'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='govt'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='other'),

        ]
        dataset.append(wetmill_data)

    table = DataTable(table_name="selling_expenses_table", dataset=dataset, table_columns=table_columns)
    return table


## Wetmill level submissions

def generate_estimated_sales_chart(season, wetmill, currency, PARCHMENT_TO_GREEN_RATIO, until_date=None):
    options = {
        'title': {
            'text': 'Estimated Sales Tracker'
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False
                },
                'stacking': 'normal'
            }
        },
    }
    parchment_sold = total_export_vol_ytd(season, [wetmill.id], currency)
    parchment_sold *= PARCHMENT_TO_GREEN_RATIO
    parchment_sold += total_local_vol_ytd(season, [wetmill.id], currency)
    
    parchment_stock = total_parchment_volume(season, [wetmill.id], currency)
    if parchment_stock < parchment_sold:
        parchment_remaining = 0
    else:
        parchment_remaining = parchment_stock - parchment_sold
    datasets = {
        'Estimated Parchment Sold': [parchment_sold],
        'Estimated Parchment Remaining' : [parchment_remaining]
    }
    labels = []
    chart = BarChart(chart_name="sales_tracker", 
        chart_labels=labels, datasets=datasets, options=options)
    
    return chart


def generate_sales_list(season, wetmill, currency, until_date=None):
    table_columns =  [
        { "title": "Sale Type" },
        { "title": "Sale" },
        { "title": "Date" },
        { "title": "Volume" },
        { "title": "Grade" },
        { "title": "Price" },
        { "title": "Adjustment" },
        { "title": "Currency" },
        { "title": "Exchange Rate" }
    ]
    
    dataset = []
    sales = IgurishaSubmission.objects.filter(season=season, wetmill=wetmill)
    sales = sales.order_by('day')
    for sale in sales:
        data = [
            sale.sale_type,
            sale.buyer,
            sale.day,
            sale.volume,
            sale.grade,
            sale.price,
            "0",
            sale.currency,
            sale.exchange_rate
        ]
        dataset.append(data)
    table_data = {
        "table_name": "sales_table",
        "dataset": dataset,
        "table_columns": table_columns
    }

    table_engine = TableEngine(**table_data)
    return table_engine.table

def generate_selling_expenses_table_single_wetmill(season, wetmill, currency, until_date=None):
    table_columns = [
        { "title": "Date"},
        { "title": "Milling" },
        { "title": "Marketing" },
        { "title": "Export" },
        { "title": "Finance" },
        { "title": "Capex" },
        { "title": "Govt" },
        { "title": "Other" }
    ]

    dataset = []
    expenses = DepanseSubmission.objects.filter(season=season, wetmill=wetmill)

    totals = [
        'Totals',
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='milling'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='marketing'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='export'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='finance'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='capex'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='govt'),
        sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='other'),
    ]
    dataset.append(totals)

    for expense in expenses:
        data = [
            expense.submission_date,
            expense.milling,
            expense.marketing,
            expense.export,
            expense.finance,
            expense.capex,
            expense.govt,
            expense.other,
        ]
        dataset.append(data)
    table = DataTable(table_name="selling_expenses_table", dataset=dataset, table_columns=table_columns)
    
    return table

def generate_sales_breakdown_chart(season, wetmill, csp, currency, until_date=None):
    wetmill_seasons = WetmillCSPSeason.objects.filter(wetmill=wetmill)
    categories = [wetmill_season.csp.id for wetmill_season in wetmill_seasons]
    similar_wetmills = WetmillCSPSeason.objects.filter(
        csp__pk__in=categories
    ).values('wetmill')
    similar_wetmills = [row['wetmill'] for row in similar_wetmills]

    labels = ['Export', 'Local']
    datasets = {wetmill.name: [
        total_export_sales_ytd(season, [wetmill.id], currency),
        total_local_sales_ytd(season, [wetmill.id], currency)
    ]}
    if similar_wetmills:
        datasets[csp.name + ' Wetmills'] = [
            total_export_sales_ytd(season, similar_wetmills, currency),
            total_local_sales_ytd(season, similar_wetmills, currency)
        ]
    datasets['All Wetmills'] = [
            total_export_sales_ytd(season, None, currency),
            total_local_sales_ytd(season, None, currency)
        ]
    
    options = {
        'title': {
            'text': 'Sale Type - Export v Local'
        }
    }
    chart = ColumnChart(chart_name="sale_type", 
        chart_labels=labels, datasets=datasets, options=options)
    return chart


def generate_selling_expenses_chart(season, wetmill, csp, currency, until_date=None):
    labels = ['Milling', 'Marketing', 'Export', 'Finance', 'Capex', 'Govt', 'Other']
    wetmill_seasons = WetmillCSPSeason.objects.filter(wetmill=wetmill)
    categories = [wetmill_season.csp.id for wetmill_season in wetmill_seasons]
    similar_wetmills = WetmillCSPSeason.objects.filter(
        csp__pk__in=categories
    ).values('wetmill')
    similar_wetmills = [row['wetmill'] for row in similar_wetmills]
    
    datasets = {
        wetmill.name: [
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='milling'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='marketing'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='export'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='finance'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='capex'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='govt'),
            sales_expenses_ytd(season, [wetmill.id], currency, selected_fields='other'),
        ]}

    if similar_wetmills:
        datasets[csp.name + ' Wetmills'] = [
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='milling'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='marketing'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='export'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='finance'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='capex'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='govt'),
            sales_expenses_ytd(season, similar_wetmills, currency, selected_fields='other')
        ]

    datasets['All Wetmills'] = [
            sales_expenses_ytd(season, None, currency, selected_fields='milling'),
            sales_expenses_ytd(season, None, currency, selected_fields='marketing'),
            sales_expenses_ytd(season, None, currency, selected_fields='export'),
            sales_expenses_ytd(season, None, currency, selected_fields='finance'),
            sales_expenses_ytd(season, None, currency, selected_fields='capex'),
            sales_expenses_ytd(season, None, currency, selected_fields='govt'),
            sales_expenses_ytd(season, None, currency, selected_fields='other'),
        ]

    options = {
        'title': {
            'text': 'Selling Expenses'
        }
    }
    chart = ColumnChart(chart_name="selling_expenses", 
        chart_labels=labels, datasets=datasets, options=options)
    return chart


def get_all_sales_messages(season, wetmill_id, until_date=None):
    return

def get_all_selling_expenses_messages(season, wetmill_id, until_date=None):
    return

