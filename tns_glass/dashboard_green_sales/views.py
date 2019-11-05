from wetmills.models import Wetmill
from smartmin.views import SmartCRUDL, SmartReadView, SmartListView
from wetmills.models import Wetmill, WetmillCSPSeason, WetmillSeasonAccountingSystem, CSP
from perms.models import has_country_permission, get_wetmills_with_permission, has_wetmill_permission
from dashboard.views import DashboardCRUDL

from locales.models import Country, Currency, Weight
from seasons.models import Season
from datetime import datetime

from sms.models import IgurishaSubmission, DepanseSubmission
from django.utils.translation import ugettext_lazy as _

from dashboard.models import load_assumptions_for_wetmills

import calculations

def is_compliance_officer(user):
    return user.groups.filter(name="Compliance Officers")

def is_admin_or_country_admin(user):
    return user.groups.filter(name="Country Administrators") or user.groups.filter(name="Administrators")

class SalesDashboardCRUDL(SmartCRUDL):
    actions = ('seasonaggregate', 'wetmillsales')
    model = Wetmill

    class Wetmillsales(SmartReadView):
        def get_allowed_seasons(self):
            allowed_seasons = []

            seasons = [_['season'] for _ in WetmillSeasonAccountingSystem.objects.all().exclude(accounting_system='NONE').values('season').distinct()]
            for season in Season.objects.filter(id__in=seasons):
                wetmills = get_wetmills_with_permission(self.request.user, season, 'sms_view')
                if wetmills:
                    season.wetmills = wetmills
                    allowed_seasons.append(season)

            return allowed_seasons

        def get_season(self):
            season_id = int(self.request.REQUEST.get('season', -1))
            for season in self.seasons:
                if season.pk == season_id:
                    return season

            return self.seasons[0]    
    
        def has_permission(self, request, *args, **kwargs):
            # Let's use the permissions for the DashboardCRUDL for now (Until we want to separate the permissions)
            
            #perm = super(DashboardCRUDL.Wetmill, self).has_permission(request, *args, **kwargs)
            self.seasons = self.get_allowed_seasons()
            if not self.seasons:
                return False

            self.season = self.get_season()
            wetmill = self.get_object()
            return wetmill in self.season.wetmills

        def get_single_wetmill_charts(self, season, selected_wetmill, csp, currency, PARCHMENT_TO_GREEN_RATIO):
            charts = []
            chart = calculations.generate_estimated_sales_chart(season, selected_wetmill, currency, PARCHMENT_TO_GREEN_RATIO)
            charts.append(chart)

            chart = calculations.generate_sales_breakdown_chart(season, selected_wetmill, csp, currency)
            charts.append(chart)

            chart = calculations.generate_selling_expenses_chart(season, selected_wetmill, csp, currency)
            charts.append(chart)
            
            return charts
        
        def get_context_data(self, *args, **kwargs):
            context = super(SalesDashboardCRUDL.Wetmillsales, self).get_context_data(*args,**kwargs)
            season = self.get_season()
            today = datetime.now().date()

            wetmill = self.object
            wetmill_ids = [wetmill.id,]
            csp = wetmill.get_csp_for_season(season)
            selected_currency = Currency.objects.get(currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))

            assumptions = load_assumptions_for_wetmills(season, [wetmill, ], self.request.user)
            PARCHMENT_GREEN_RATIO = assumptions.get(wetmill.id).parchment_green_ratio

            total_sales_ytd = calculations.total_sales_ytd(season, wetmill_ids, selected_currency)
            avg_sales_price = calculations.average_sales_price_ytd(season, wetmill_ids, selected_currency)
            sales_expenses_ytd = calculations.sales_expenses_ytd(season, wetmill_ids, selected_currency)
            estmated_parchment_vol_remaining = calculations.estmated_parchment_vol_remaining(season, wetmill_ids, selected_currency, PARCHMENT_GREEN_RATIO)
            estimated_percent_sold_ytd = calculations.estimated_percent_sold_ytd(season, wetmill_ids, selected_currency, PARCHMENT_GREEN_RATIO)

            total_export_sales_ytd = calculations.total_export_sales_ytd(season, wetmill_ids, selected_currency)
            avg_export_sales_price = calculations.average_export_sales_price_ytd(season, wetmill_ids, selected_currency)
            total_export_vol_ytd = calculations.total_export_vol_ytd(season, wetmill_ids, selected_currency)
            percent_of_total_sales_revenue = calculations.percent_of_total_sales_revenue(season, wetmill_ids, selected_currency)

            total_local_sales_ytd = calculations.total_local_sales_ytd(season, wetmill_ids, selected_currency)
            average_local_sales_ytd = calculations.average_local_sales_ytd(season, wetmill_ids, selected_currency)
            total_local_vol_ytd = calculations.total_local_vol_ytd(season, wetmill_ids, selected_currency)
            percent_of_local_sales_vol = calculations.percent_of_local_sales_vol(season, wetmill_ids, selected_currency)

            currencies = ['USD', 'BR']
            tables = []

            show_multiple = False
            sales_table = calculations.generate_sales_list(season, wetmill, selected_currency)
            selling_expenses_table = calculations.generate_selling_expenses_table_single_wetmill(season, wetmill, selected_currency)
            charts = self.get_single_wetmill_charts(season, wetmill, csp, selected_currency, PARCHMENT_GREEN_RATIO)

            context.update({
                'currencies': currencies,
                'tables': tables,
                'charts': charts,
                'sales_table': sales_table,
                'selling_expenses_table': selling_expenses_table,
                'show_multiple': show_multiple,
                'selected_currency': selected_currency,
                'total_sales_ytd': total_sales_ytd,
                'avg_sales_price': avg_sales_price,
                'sales_expenses_ytd': sales_expenses_ytd,
                'estmated_parchment_vol_remaining': estmated_parchment_vol_remaining,
                'estimated_percent_sold_ytd': estimated_percent_sold_ytd,
                'total_export_sales_ytd': total_export_sales_ytd,
                'avg_export_sales_price': avg_export_sales_price,
                'total_export_vol_ytd': total_export_vol_ytd,
                'percent_of_total_sales_revenue': percent_of_total_sales_revenue,
                'total_local_sales_ytd': total_local_sales_ytd,
                'average_local_sales_ytd': average_local_sales_ytd,
                'total_local_vol_ytd': total_local_vol_ytd,
                'percent_of_local_sales_vol': percent_of_local_sales_vol
            })

            accounting_system = wetmill.get_accounting_for_season(season)
            context['accounting_system'] = accounting_system
            context['local'] = season.country.currency
            context['exchange_rate'] = 1
            context['currency'] = Currency.objects.get(currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))
            
            if context['currency'] != context['local']:
                context['exchange_rate'] = season.exchange_rate
            
            context['season'] = season
            context['csp'] = csp
            context['seasons'] = [_ for _ in self.seasons if _.country == wetmill.country]

            context['local_weight'] = season.country.weight
            context['kilograms'] = Weight.objects.get(name__iexact="Kilograms")
            context['weight'] = Weight.objects.get(abbreviation__iexact=self.request.REQUEST.get('weight', season.country.weight.abbreviation))
            context['dashboard_weight'] = Weight.objects.get(abbreviation__iexact='mT')

            if context['kilograms'] != context['weight']:
                context['dashboard_weight'] = context['weight']

            context['show_compliance_only'] = is_compliance_officer(self.request.user)
            context['is_admin_or_country_admin'] = is_admin_or_country_admin(self.request.user)

            return context
    
    class Seasonaggregate(SmartListView):
        def get_allowed_seasons(self):
            allowed_seasons = []

            seasons = [_['season'] for _ in
                       WetmillSeasonAccountingSystem.objects.all().exclude(accounting_system='NONE').values(
                           'season').distinct()]
            for season in Season.objects.filter(id__in=seasons):
                wetmills = get_wetmills_with_permission(self.request.user, season, 'sms_view')
                if wetmills:
                    season.wetmills = wetmills
                    allowed_seasons.append(season)

            return allowed_seasons

        def get_season(self):
            season_id = int(self.request.REQUEST.get('season', -1))
            for season in self.seasons:
                if season.pk == season_id:
                    return season

            return self.seasons[0]

        def derive_queryset(self, *args, **kwargs):
            season = self.get_season()
            queryset = season.wetmills

            if self.search_fields and 'search' in self.request.REQUEST:
                terms = self.request.REQUEST['search'].split()

                query = Q(pk__gt=0)
                for term in terms:
                    term_query = Q(pk__lt=0)
                    for field in self.search_fields:
                        term_query |= Q(**{ field: term })

                    # this term could also be in the CSP name
                    csps = CSP.objects.filter(Q(name__icontains=term)|Q(sms_name__icontains=term))
                    wetmill_ids = [_.wetmill.id for _ in WetmillCSPSeason.objects.filter(season=season, csp__in=csps)]
                    term_query |= Q(id__in=wetmill_ids)

                    query &= term_query

                queryset = queryset.filter(query)

            wetmill_ids = [_.wetmill_id for _ in WetmillSeasonAccountingSystem.objects.filter(season=season,
                                                                                accounting_system__in=['2012', 'LIT2', 'GTWB'])]
            queryset = queryset.filter(is_active=True, id__in=wetmill_ids)
            return queryset

        def has_permission(self, request, *args, **kwargs):
            self.seasons = self.get_allowed_seasons()
            if not self.seasons:
                return False

            self.season = self.get_season()
            self.permitted_wetmills = self.season.wetmills
            return len(self.permitted_wetmills) > 0

        def derive_title(self):
            season = self.get_season()
            return _("SMS Dashboard - %s %s") % (season.country.name, season.name)

        def order_queryset(self, queryset):
            # we do our ordering in our context data
            return queryset

        def get_multiple_wetmill_tables(self, season, expenses_wetmills, sales_wetmills, currency):
            tables = []
            sales_table = calculations.generate_sales_table(season, sales_wetmills, currency)
            tables.append(sales_table)

            expenses_table = calculations.generate_selling_expenses_table(season, expenses_wetmills, currency)
            tables.append(expenses_table)

            return tables

        def get_context_data(self, *args, **kwargs):
            context = super(SalesDashboardCRUDL.Seasonaggregate, self).get_context_data(*args, **kwargs)
            season = self.get_season()
            today = datetime.now().date()

            sales_wetmills_messages = IgurishaSubmission.objects.filter(season=season).order_by('wetmill')
            sales_wetmills_ids = [w.wetmill_id for w in sales_wetmills_messages]
            sales_wetmills = Wetmill.objects.filter(pk__in=sales_wetmills_ids)
            

            expenses_wetmills_messages = DepanseSubmission.objects.filter(season=season).order_by('wetmill')
            expenses_wetmills_ids = [w.wetmill_id for w in expenses_wetmills_messages]
            expenses_wetmills = Wetmill.objects.filter(pk__in=expenses_wetmills_ids)

            wetmill_csp_mappings = dict()
            for wetmill_csp in WetmillCSPSeason.objects.filter(season=season).select_related('csp', 'wetmill'):
                wetmill_csp_mappings[wetmill_csp.wetmill.id] = wetmill_csp.csp

            wetmill_ids = []
            if(sales_wetmills.count()):
                wetmill_ids += sales_wetmills_ids
            if expenses_wetmills.count():
                wetmill_ids += expenses_wetmills_ids

            if len(wetmill_ids) > 0:
                wetmill_ids = list(set(wetmill_ids)) # We only want distinct values.

            selected_currency = Currency.objects.get(
                currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))

            total_sales_ytd = calculations.total_sales_ytd(season, wetmill_ids, selected_currency)
            avg_sales_price = calculations.average_sales_price_ytd(season, wetmill_ids, selected_currency)
            sales_expenses_ytd = calculations.sales_expenses_ytd(season, wetmill_ids, selected_currency)
            estmated_parchment_vol_remaining = calculations.estmated_parchment_vol_remaining(season, wetmill_ids,
                                                                                             selected_currency, self.request.user)
            estimated_percent_sold_ytd = calculations.estimated_percent_sold_ytd(season, wetmill_ids, selected_currency, self.request.user)

            total_export_sales_ytd = calculations.total_export_sales_ytd(season, wetmill_ids, selected_currency)
            avg_export_sales_price = calculations.average_export_sales_price_ytd(season, wetmill_ids, selected_currency)
            total_export_vol_ytd = calculations.total_export_vol_ytd(season, wetmill_ids, selected_currency)
            percent_of_total_sales_revenue = calculations.percent_of_total_sales_revenue(season, wetmill_ids,
                                                                                         selected_currency)

            total_local_sales_ytd = calculations.total_local_sales_ytd(season, wetmill_ids, selected_currency)
            average_local_sales_ytd = calculations.average_local_sales_ytd(season, wetmill_ids, selected_currency)
            total_local_vol_ytd = calculations.total_local_vol_ytd(season, wetmill_ids, selected_currency)
            percent_of_local_sales_vol = calculations.percent_of_local_sales_vol(season, wetmill_ids, selected_currency)

            currencies = ['USD', 'BR']
            charts = []
            sales_table = None

            show_multiple = True
            tables = self.get_multiple_wetmill_tables(season, expenses_wetmills, sales_wetmills, selected_currency)

            context.update({
                'currencies': currencies,
                'tables': tables,
                'charts': charts,
                'sales_table': sales_table,
                'show_multiple': show_multiple,
                'selected_currency': selected_currency,
                'total_sales_ytd': total_sales_ytd,
                'avg_sales_price': avg_sales_price,
                'sales_expenses_ytd': sales_expenses_ytd,
                'estmated_parchment_vol_remaining': estmated_parchment_vol_remaining,
                'estimated_percent_sold_ytd': estimated_percent_sold_ytd,
                'total_export_sales_ytd': total_export_sales_ytd,
                'avg_export_sales_price': avg_export_sales_price,
                'total_export_vol_ytd': total_export_vol_ytd,
                'percent_of_total_sales_revenue': percent_of_total_sales_revenue,
                'total_local_sales_ytd': total_local_sales_ytd,
                'average_local_sales_ytd': average_local_sales_ytd,
                'total_local_vol_ytd': total_local_vol_ytd,
                'percent_of_local_sales_vol': percent_of_local_sales_vol
            })

            context['local'] = season.country.currency
            context['exchange_rate'] = 1
            context['currency'] = Currency.objects.get(
                currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))

            if context['currency'] != context['local']:
                context['exchange_rate'] = season.exchange_rate

            context['season'] = season
            context['seasons'] = self.seasons

            context['local_weight'] = season.country.weight
            context['kilograms'] = Weight.objects.get(name__iexact="Kilograms")
            context['weight'] = Weight.objects.get(
                abbreviation__iexact=self.request.REQUEST.get('weight', season.country.weight.abbreviation))
            context['dashboard_weight'] = Weight.objects.get(abbreviation__iexact='mT')

            if context['kilograms'] != context['weight']:
                context['dashboard_weight'] = context['weight']

            context['show_compliance_only'] = is_compliance_officer(self.request.user)
            context['is_admin_or_country_admin'] = is_admin_or_country_admin(self.request.user)

            return context
