from datetime import datetime, timedelta
from decimal import Decimal
from csps.models import CSP
from dashboard.models import build_wetmill_data, calculate_cp_chart, calculate_expenses_chart, Assumptions, build_stock_data, build_finance_data, build_compliance_data, calculate_totals, calculate_predicted_cherry_curve, convert_weekly_to_total, PredictedOutput, calculate_actual_cherry_curve, calculate_price_chart, calculate_estimated_total_parchment_value_curve, calculate_estimated_stored_parchment_value_curve, calculate_working_capital_curve, remove_current_datapoint, convert_to_usd, calculate_performance_alerts, adjust_currency_per_weight_values
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from rapidsms_httprouter.models import Message
from sms.models import IbitumbweSubmission, AmafarangaSubmission, SitokiSubmission, TwakinzeSubmission, WetmillObserver, CPO, Accountant, Farmer
from sms.views import add_sms_data_to_context
from smartmin.views import SmartCRUDL, SmartReadView, SmartListView, SmartUpdateView, SmartTemplateView, SmartXlsView
from wetmills.models import Wetmill, WetmillCSPSeason, WetmillSeasonAccountingSystem
from seasons.models import Season
from locales.models import Country, Currency, Weight
from perms.models import has_country_permission, get_wetmills_with_permission, has_wetmill_permission
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _

def is_compliance_officer(user):
    return user.groups.filter(name="Compliance Officers")

def is_admin_or_country_admin(user):
    return user.groups.filter(name="Country Administrators") or user.groups.filter(name="Administrators")

class DashboardCRUDL(SmartCRUDL):
    actions = ('dashboard', 'wetmill', 'wetmillexport', 'dashboardexport')
    model = Wetmill

    class Wetmill(SmartReadView):

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
            perm = super(DashboardCRUDL.Wetmill, self).has_permission(request, *args, **kwargs)
            self.seasons = self.get_allowed_seasons()
            if not self.seasons:
                return False

            self.season = self.get_season()
            wetmill = self.get_object()
            return wetmill in self.season.wetmills

        def derive_title(self):
            season = self.get_season()
            return "%s - %s" % (self.object.name, season.name)

        def calculate_amafaranga_submissions(self, wetmill, season, wetmill_data):
            submission_type = "Amafaranga"
            submissions = AmafarangaSubmission.objects.filter(wetmill=wetmill, season=season, active=True).order_by('start_of_week')
            totals = []

            season_start = wetmill_data['season_start']

        def calculate_totals(self, entries):
            totals = list()

            # calculate our totals
            for (row_index, row) in enumerate(entries):
                for (col_index, col) in enumerate(row.get('values', [])):
                    while col_index >= len(totals):
                        totals.append(None)

                    if col.get('total', False):
                        total = totals[col_index]
                        if total is None:
                            total = Decimal(0)
                        totals[col_index] = total + col.get('value', Decimal(0))

                    if col.get('last', False) and totals[col_index] is None:
                        totals[col_index] = col.get('value', None)

            return totals

        def build_submission_data(self, wetmill, season, wetmill_data, context):
            accounting_system = wetmill.get_accounting_for_season(season)
            if accounting_system != '2012' and accounting_system != 'LIT2' and accounting_system != 'GTWB':
                add_sms_data_to_context(self.request, context, wetmill, season)
            else:
                submissions = list()

                # first lets add all the cash messages
                balance = Decimal(0)
                entries = []
                columns = [dict(label=_("Day")),
                           dict(label=_("Cash Advance"), currency=True),
                           dict(label=_("Cash Returned"), currency=True),
                           dict(label=_("Cash Spent"), currency=True),
                           dict(label=_("Credit Spent"), currency=True),
                           dict(label=_("Cherry"), weight=True),
                           dict(label=_("Balance"), currency=True),
                           dict(label=_("Cherry Price"), currency=True),
                           dict(label=_("Submitted"))]
                missing = 0
                previous = wetmill_data['season_day_start'] - timedelta(days=1)
                twakinze = list(TwakinzeSubmission.objects.filter(active=True, wetmill=wetmill, season=season).order_by('report_day').select_related('submission'))

                for sub in IbitumbweSubmission.objects.filter(active=True, wetmill=wetmill, season=season).order_by('report_day').select_related('submission'):
                    while (sub.report_day - previous).days > 1:
                        previous = previous + timedelta(days=1)

                        while twakinze and twakinze[0].report_day < previous:
                            twakinze.pop(0)

                        if twakinze and twakinze[0].report_day == previous:
                            data = list()
                            data.append(dict(value=twakinze[0].report_day, display_class='date'))
                            data.append(dict(value=_("Wetmill Reported as Closed"), colspan=6))
                            data.append(dict(value=""))
                            if twakinze[0].submission:
                                data.append(dict(value=twakinze[0].submission.created, display_class='date'))
                            else:
                                data.append(dict(value=twakinze[0].created_by, display_class='user'))

                            entries.append(dict(type='twakinze', values=data, edit_url=reverse('sms.twakinzesubmission_create') + "?template=%d" % twakinze[0].pk))
                            twakinze.pop(0)
                        else:
                            entries.append(dict(type='missing_daily', date=previous))
                            missing += 1

                    data = list()
                    data.append(dict(value=sub.report_day, display_class='date'))
                    data.append(dict(value=sub.cash_advanced, total=True, currency=True))
                    data.append(dict(value=sub.cash_returned, total=True, currency=True))
                    data.append(dict(value=sub.cash_spent, total=True, currency=True))
                    data.append(dict(value=sub.credit_spent, total=True, currency=True))
                    data.append(dict(value=sub.cherry_purchased, total=True, weight=True))

                    balance += sub.cash_advanced - sub.cash_returned - sub.cash_spent - sub.credit_spent
                    data.append(dict(value=balance, display_class='calculated', currency=True))

                    cherry_price = Decimal(0)
                    if sub.cherry_purchased > 0:
                        cherry_price = (sub.cash_spent + sub.credit_spent) * context['weight'].ratio_to_kilogram / sub.cherry_purchased
                    data.append(dict(value=cherry_price, currency=True, display_class='calculated'))

                    if sub.submission:
                        data.append(dict(value=sub.submission.created, display_class='date'))
                    else:
                        data.append(dict(value=sub.created_by, display_class='user'))

                    entries.append(dict(type='ibitumbwe', values=data, edit_url=reverse('sms.ibitumbwesubmission_create') + "?template=%d" % sub.pk))
                    previous = sub.report_day

                while previous < wetmill_data['season_ideal_last_daily']:
                    previous = previous + timedelta(days=1)

                    while twakinze and twakinze[0].report_day < previous:
                        twakinze.pop(0)

                    if twakinze and twakinze[0].report_day == previous:
                        data = list()
                        data.append(dict(value=twakinze[0].report_day, display_class='date'))
                        data.append(dict(value=_("Wetmill Reported as Closed"), colspan=6))
                        data.append(dict(value=""))
                        if twakinze[0].submission:
                            data.append(dict(value=twakinze[0].submission.created, display_class='date'))
                        else:
                            data.append(dict(value=twakinze[0].created_by, display_class='user'))

                        entries.append(dict(type='twakinze', values=data, edit_url=reverse('sms.twakinzesubmission_create') + "?template=%d" % twakinze[0].pk))
                        twakinze.pop(0)
                    else:
                        entries.append(dict(type='missing_daily', date=previous))
                        missing += 1

                totals = self.calculate_totals(entries)
                avg_cherry_price = Decimal(0)
                if totals and len(totals) > 5:
                    if totals[5]:
                        avg_cherry_price = ((totals[3] + totals[4]) * context['weight'].ratio_to_kilogram / totals[5])
                    totals[7] = avg_cherry_price

                # set our totals
                for i, col in enumerate(columns):
                    if i < len(totals):
                        col['total'] = totals[i]

                entries.reverse()

                submissions.append(dict(name=_("Daily"),
                                        tab_name="daily",
                                        type='ibitumbwe',
                                        entries=entries,
                                        columns=columns,
                                        missing=missing,
                                        count=len(entries) - missing,
                                        ideal=len(entries)))

                entries = []
                columns = [dict(label=_("Week")),
                           dict(label=_("Opening Balance"), currency=True),
                           dict(label=_("Working Capital"), currency=True),
                           dict(label=_("Income"), currency=True),
                           dict(label=_("Advanced"), currency=True),
                           dict(label=_("Full Time Labor"), currency=True),
                           dict(label=_("Casual Labor"), currency=True),
                           dict(label=_("Commission"), currency=True),
                           dict(label=_("Transport"), currency=True),
                           dict(label=_("Other Expenses"), currency=True),
                           dict(label=_("Closing Balance"), currency=True),
                           dict(label=_("Variance"), currency=True),
                           dict(label=_("Submitted"))]
                previous = wetmill_data['season_week_start'] - timedelta(days=7)
                previous_closing_balance = None
                missing = 0

                if accounting_system == '2012' or accounting_system == 'GTWB':

                    for sub in AmafarangaSubmission.objects.filter(active=True, wetmill=wetmill, season=season).order_by('start_of_week').select_related('submission'):
                        while (sub.start_of_week - previous).days > 7:
                            previous = previous + timedelta(days=7)
                            entries.append(dict(type='missing_amafaranga', date=previous, end_date=previous + timedelta(days=7)))
                            missing += 1

                        data = list()
                        data.append(dict(value=sub.start_of_week, end_value=sub.start_of_week + timedelta(days=7), display_class='week'))
                        data.append(dict(value=sub.opening_balance, currency=True))
                        data.append(dict(value=sub.working_capital, currency=True, total=True))
                        data.append(dict(value=sub.other_income, currency=True, total=True))
                        data.append(dict(value=sub.advanced, currency=True, total=True))
                        data.append(dict(value=sub.full_time_labor, currency=True, total=True))
                        data.append(dict(value=sub.casual_labor, currency=True, total=True))
                        data.append(dict(value=sub.commission, currency=True, total=True))
                        data.append(dict(value=sub.transport, currency=True, total=True))
                        data.append(dict(value=sub.other_expenses, currency=True, total=True))

                        closing_balance = sub.get_closing_balance()
                        data.append(dict(value=closing_balance, currency=True, display_class='calculated'))

                        variance = 0
                        if previous_closing_balance is not None:
                            variance = previous_closing_balance - sub.opening_balance
                        data.append(dict(value=variance, currency=True, display_class='calculated'))

                        if sub.submission:
                            data.append(dict(value=sub.submission.created, display_class='date'))
                        else:
                            data.append(dict(value=sub.created_by, display_class='user'))

                        entries.append(dict(type='amafaranga', values=data, edit_url=reverse('sms.amafarangasubmission_create') + "?template=%d" % sub.pk))
                        previous = sub.start_of_week
                        previous_closing_balance = closing_balance

                    while previous + timedelta(days=7) < wetmill_data['season_ideal_last_weekly']:
                        previous = previous + timedelta(days=7)
                        entries.append(dict(type='missing_amafaranga', date=previous, end_date=previous + timedelta(days=7)))
                        missing += 1

                    entries.reverse()

                    totals = self.calculate_totals(entries)
                    for i, col in enumerate(columns):
                        if i < len(totals):
                            col['total'] = totals[i]

                    submissions.append(dict(name=_("Cash"),
                                            tab_name='cash',
                                            type='amafaranga',
                                            currency=True,
                                            entries=entries,
                                            columns=columns,
                                            missing=missing,
                                            count=len(entries) - missing,
                                            ideal=len(entries)))

                    entries = []
                    columns = [dict(label=_("Week")),
                               dict(label=_("Grade A Stored"), weight=True),
                               dict(label=_("Grade B Stored"), weight=True),
                               dict(label=_("Grade C Stored"), weight=True),
                               dict(label=_("Grade A Shipped"), weight=True),
                               dict(label=_("Grade B Shipeed"), weight=True),
                               dict(label=_("Grade C Shipped"), weight=True),
                               dict(label=_("Total Stored"), weight=True),
                               dict(label=_("Total Shipped"), weight=True),
                               dict(label=_("In Store"), weight=True),
                               dict(label=_("Submitted"))]
                    previous = wetmill_data['season_week_start'] - timedelta(days=7)
                    missing = 0

                    total_stored = Decimal(0)
                    total_shipped = Decimal(0)

                    for sub in SitokiSubmission.objects.filter(active=True, wetmill=wetmill, season=season).order_by('start_of_week').select_related('submission'):
                        while (sub.start_of_week - previous).days > 7:
                            previous = previous + timedelta(days=7)
                            entries.append(dict(type='missing_sitoki', date=previous, end_date=previous + timedelta(days=7)))
                            missing += 1

                        data = list()
                        data.append(dict(value=sub.start_of_week, end_value=sub.start_of_week + timedelta(days=7), display_class='week'))
                        data.append(dict(value=sub.grade_a_stored, total=True, weight=True))
                        data.append(dict(value=sub.grade_b_stored, total=True, weight=True))
                        data.append(dict(value=sub.grade_c_stored, total=True, weight=True))
                        data.append(dict(value=sub.grade_a_shipped, total=True, weight=True))
                        data.append(dict(value=sub.grade_b_shipped, total=True, weight=True))
                        data.append(dict(value=sub.grade_c_shipped, total=True, weight=True))

                        total_stored += sub.grade_a_stored + sub.grade_b_stored + sub.grade_c_stored
                        total_shipped += sub.grade_a_shipped + sub.grade_b_shipped + sub.grade_c_shipped
                        data.append(dict(value=total_stored, display_class='calculated', last=True, weight=True))
                        data.append(dict(value=total_shipped, display_class='calculated', last=True, weight=True))
                        data.append(dict(value=total_stored - total_shipped, display_class='calculated', weight=True))

                        if sub.submission:
                            data.append(dict(value=sub.submission.created, display_class='date'))
                        else:
                            data.append(dict(value=sub.created_by, display_class='user'))

                        entries.append(dict(type='sitoki', values=data, edit_url=reverse('sms.sitokisubmission_create') + "?template=%d" % sub.pk))
                        previous = sub.start_of_week

                    while previous + timedelta(days=7) < wetmill_data['season_ideal_last_weekly']:
                        previous = previous + timedelta(days=7)
                        entries.append(dict(type='missing_sitoki', date=previous, end_date=previous + timedelta(days=7)))
                        missing += 1

                    entries.reverse()

                    totals = self.calculate_totals(entries)
                    for i, col in enumerate(columns):
                        if i < len(totals):
                            col['total'] = totals[i]

                    submissions.append(dict(name=_("Stock"),
                                            tab_name='stock',
                                            type='sitoki',
                                            entries=entries,
                                            columns=columns,
                                            missing=missing,
                                            count=len(entries) - missing,
                                            ideal=len(entries)))

                context['submissions'] = submissions

                context['observers'] = WetmillObserver.objects.filter(wetmill=wetmill)
                context['cpos'] = CPO.objects.filter(wetmill=wetmill)
                context['farmers'] = Farmer.objects.filter(wetmill=wetmill)
                try:
                    context['accountant'] = Accountant.objects.get(wetmill=wetmill)
                    context['sms_messages'] = Message.objects.filter(connection=context['accountant'].connection,
                                                                     date__gte=wetmill_data['season_start'],
                                                                     date__lte=wetmill_data['season_end']).order_by('-date', '-pk')
                except Accountant.DoesNotExist:
                    pass

                context['accounting_system'] = accounting_system
                context['can_edit'] = has_wetmill_permission(self.request.user, wetmill, 'sms_edit')
                context['can_edit_wetmill'] = has_wetmill_permission(self.request.user, wetmill, 'update')

        def get_context_data(self, *args, **kwargs):
            context = super(DashboardCRUDL.Wetmill, self).get_context_data(*args, **kwargs)
            season = self.get_season()
            today = datetime.now().date()

            # the season wetmills we are comparing to
            wetmill = self.object
            wetmills = [_['wetmill'] for _ in IbitumbweSubmission.objects.filter(season=season).order_by('wetmill').values('wetmill').distinct()]
            wetmills.append(self.object.id)
            wetmills = Wetmill.objects.filter(pk__in=wetmills)
            csp = wetmill.get_csp_for_season(season)

            season_data = build_wetmill_data(season, wetmills, self.request.user)

            context['active_tab'] = self.request.REQUEST.get('active_tab', None)

            # build another array of just our single wetmill
            wetmill_data = [_ for _ in season_data if _['wetmill'].pk == wetmill.pk]

            context['local_weight'] = season.country.weight
            context['kilograms'] = Weight.objects.get(name__iexact="Kilograms")
            context['weight'] = Weight.objects.get(abbreviation__iexact=self.request.REQUEST.get('weight', season.country.weight.abbreviation))
            context['dashboard_weight'] = Weight.objects.get(abbreviation__iexact='mT')

            if context['kilograms'] != context['weight']:
                context['dashboard_weight'] = context['weight']

            context['predicted_weekly'] = calculate_predicted_cherry_curve(season, wetmill_data)
            context['actual_weekly'] = calculate_actual_cherry_curve(season, wetmill_data)

            context['predicted_total'] = convert_weekly_to_total(context['predicted_weekly'])
            context['actual_total'] = convert_weekly_to_total(context['actual_weekly'])

            context['current_weekly'] = remove_current_datapoint(context, 'actual_weekly')
            context['current_total'] = remove_current_datapoint(context, 'actual_total')

            context['wetmill_expenses'] = calculate_expenses_chart(season, wetmill_data)
            context['season_expenses'] = calculate_expenses_chart(season, season_data)

            context['cp_ratios'] = calculate_cp_chart(season, wetmill)

            csp_wetmills = [dict(wetmill=_.wetmill) for _ in WetmillCSPSeason.objects.filter(season=season, csp=csp).prefetch_related('wetmill')]
            context['csp_expenses'] = calculate_expenses_chart(season, csp_wetmills)

            (context['wetmill_prices'], context['nyc_prices']) = calculate_price_chart(season, wetmill_data[0])

            context['wetmill_parchment_estimated_total_values'] = calculate_estimated_total_parchment_value_curve(season, wetmill, self.request.user)
            context['wetmill_parchment_estimated_stored_values'] = calculate_estimated_stored_parchment_value_curve(season, wetmill, self.request.user)
            context['wetmill_working_capital_values'] = calculate_working_capital_curve(season, wetmill, self.request.user)

            context['newline'] = '\n'
            context['local'] = season.country.currency
            context['usd'] = Currency.objects.get(currency_code__iexact='USD')
            context['currency'] = Currency.objects.get(currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))

            context['exchange_rate'] = 1
            if context['currency'] != context['local']:
                context['exchange_rate'] = season.exchange_rate

            context['season'] = season
            context['csp'] = csp
            context['seasons'] = [_ for _ in self.seasons if _.country == wetmill.country]

            single_wetmill = [_ for _ in wetmills if _.pk == wetmill.pk]

            (stock_fields, wetmill_data) = build_stock_data(season, single_wetmill, today, self.request.user)
            (finance_fields, wetmill_data) = build_finance_data(season, wetmill_data, single_wetmill, today, self.request.user)
            (compliance_fields, wetmill_data) = build_compliance_data(season, wetmill_data, single_wetmill, today, self.request.user)


            if context['kilograms'] != context['weight']:
                context['dashboard_weight'] = context['weight']
                adjust_currency_per_weight_values(context['weight'], wetmill_data)

            context['wetmill_data'] = wetmill_data[0] if wetmill_data else dict()
            context['assumptions'] = wetmill_data[0]['assumptions']
            context['wetmills'] = [self.object]

            context['show_compliance_only'] = is_compliance_officer(self.request.user)
            context['is_admin_or_country_admin'] = is_admin_or_country_admin(self.request.user)
            context['can_edit_assumptions'] = Assumptions.can_edit(season, wetmill.get_csp_for_season(season), wetmill, self.request.user)
            self.build_submission_data(wetmill, season, context['wetmill_data'], context)

            return context

    class SubmissionExport(object):

        def render_to_response(self, context, **response_kwargs):
            from xlwt import Workbook
            book = Workbook()

            wetmills = context['wetmills']
            season = context['season']

            csp_wetmills = dict((_.wetmill_id, _.csp.name) for _ in WetmillCSPSeason.objects.filter(season=season).prefetch_related('csp'))

            submission_types = (dict(sheet="Closed", model=TwakinzeSubmission, ordering='report_day'),
                                dict(sheet="Daily", model=IbitumbweSubmission, ordering='report_day'),
                                dict(sheet="Cash", model=AmafarangaSubmission, ordering='start_of_week'),
                                dict(sheet="Stock", model=SitokiSubmission, ordering='start_of_week'))

            for submission_type in submission_types:
                sheet = book.add_sheet(str(submission_type['sheet']))

                # build up our header row
                sheet.write(0, 0, "CSP")
                for (col, label) in enumerate(submission_type['model'].EXPORT_FIELDS):
                    if label.get('weight', False):
                        sheet.write(0, col+1, unicode(label['label']) + " (%s)" % context['kilograms'].abbreviation)
                    elif label.get('currency', False):
                        sheet.write(0, col+1, unicode(label['label']) + " (%s)" % season.country.currency.abbreviation)
                    else:
                        sheet.write(0, col+1, unicode(label['label']))

                # then our actual values
                row = 1
                submissions = submission_type['model'].objects.filter(season=season, wetmill__in=wetmills).select_related('wetmill').order_by(submission_type['ordering'])
                for submission in submissions:
                    for (col, field) in enumerate(submission_type['model'].EXPORT_FIELDS):
                        if col == 0:
                            csp = csp_wetmills.get(submission.wetmill_id, "")
                            sheet.write(row, 0, csp)

                        value = getattr(submission, field['field'], None)

                        if value is None: value = ""

                        sheet.write(row, col+1, str(value))
                    row += 1

            # Create the HttpResponse object with the appropriate header.
            response = HttpResponse(mimetype='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s.xls' % (self.get_filename(context))
            book.save(response)
            return response

    class Wetmillexport(SubmissionExport, Wetmill):

        def get_filename(self, context):
            season = context['season']
            wetmill = context['object']
            return "%s_%s" % (season.name, wetmill.name)

    class Dashboard(SmartListView):
        paginate_by = None
        search_fields = ('name__icontains',)
        permission = None

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
                if season.id == season_id:
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

        def get_context_data(self, *args, **kwargs):
            context = super(DashboardCRUDL.Dashboard, self).get_context_data(*args, **kwargs)
            season = self.get_season()

            today = datetime.now().date()

            context['active_tab'] = self.request.REQUEST.get('active_tab', None)

            context['local'] = season.country.currency
            context['usd'] = Currency.objects.get(currency_code__iexact='USD')
            context['currency'] = Currency.objects.get(currency_code__iexact=self.request.REQUEST.get('currency', season.country.currency.currency_code))

            context['exchange_rate'] = 1
            if context['currency'] != context['local']:
                context['exchange_rate'] = season.exchange_rate

            context['local_weight'] = season.country.weight
            context['kilograms'] = Weight.objects.get(name__iexact="Kilograms")
            context['weight'] = Weight.objects.get(abbreviation__iexact=self.request.REQUEST.get('weight', season.country.weight.abbreviation))
            context['dashboard_weight'] = Weight.objects.get(abbreviation__iexact='mT')

            all_wetmills = context['object_list']
            active_wetmills = IbitumbweSubmission.objects.filter(season=season).order_by('wetmill').values('wetmill').distinct()

            wetmills = all_wetmills.filter(pk__in=active_wetmills)
            inactive_wetmills = all_wetmills.exclude(pk__in=active_wetmills)

            wetmill_csp_mappings = dict()
            for wetmill_csp in WetmillCSPSeason.objects.filter(season=season).select_related('csp', 'wetmill'):
                wetmill_csp_mappings[wetmill_csp.wetmill.id] = wetmill_csp.csp
            for inactive in inactive_wetmills:
                if inactive.id in wetmill_csp_mappings:
                    inactive.csp = wetmill_csp_mappings[inactive.id]

            context['object_list'] = wetmills
            context['wetmills'] = wetmills
            context['inactive'] = inactive_wetmills
            context['full_wetmill_count'] = len(wetmills) + len(inactive_wetmills)

            (stock_fields, wetmill_data) = build_stock_data(season, context['object_list'], today, self.request.user)
            (finance_fields, wetmill_data) = build_finance_data(season, wetmill_data, context['object_list'], today, self.request.user)
            (compliance_fields, wetmill_data) = build_compliance_data(season, wetmill_data, context['object_list'], today, self.request.user)
            calculate_performance_alerts(season, wetmill_data)


            if context['kilograms'] != context['weight']:
                context['dashboard_weight'] = context['weight']
                adjust_currency_per_weight_values(context['weight'], wetmill_data)

            if context['currency'] == context['usd']:
                convert_to_usd(season, wetmill_data)

            sort_column = self.request.REQUEST.get('_order', 'wetmill')
            reverse = False
            if sort_column[0] == '-':
                reverse = True
                sort_column = sort_column[1:]

            wetmill_data = sorted(wetmill_data, key=lambda data: data['wetmill'].name.lower() if sort_column == 'wetmill' else data.get(sort_column, Decimal(0)))
            if reverse:
                wetmill_data.reverse()

            context['wetmill_data'] = wetmill_data

            context['stock_fields'] = stock_fields
            context['stock_totals'] = calculate_totals(stock_fields, wetmill_data)

            context['finance_fields'] = finance_fields
            context['finance_totals'] = calculate_totals(finance_fields, wetmill_data)

            context['compliance_fields'] = compliance_fields
            context['compliance_totals'] = calculate_totals(compliance_fields, wetmill_data)

            context['order_by'] = sort_column
            context['reverse'] = reverse

            context['predicted_weekly'] = calculate_predicted_cherry_curve(season, wetmill_data)
            context['actual_weekly'] = calculate_actual_cherry_curve(season, wetmill_data)

            context['predicted_total'] = convert_weekly_to_total(context['predicted_weekly'])
            context['actual_total'] = convert_weekly_to_total(context['actual_weekly'])

            context['current_weekly'] = remove_current_datapoint(context, 'actual_weekly')
            context['current_total'] = remove_current_datapoint(context, 'actual_total')

            context['newline'] = '\n'

            context['editable_assumptions'] = Assumptions.get_editable_assumptions_for_season(season, self.request.user)
            context['show_compliance_only'] = is_compliance_officer(self.request.user)

            country_ids = []
            for country in Country.objects.all():
                if has_country_permission(self.request.user, country, 'sms_view'):
                    country_ids.append(country.pk)

            context['season'] = season
            context['seasons'] = self.seasons

            return context

    class Dashboardexport(SubmissionExport, Dashboard):
        def get_filename(self, context):
            season = context['season']
            return "%s_season" % season.name

class OutputForm(forms.ModelForm):
    week_1 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 1"))
    week_2 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 2"))
    week_3 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 3"))
    week_4 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 4"))
    week_5 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 5"))
    week_6 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 6"))
    week_7 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 7"))
    week_8 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 8"))
    week_9 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 9"))
    week_10 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 10"))
    week_11 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 11"))
    week_12 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 12"))
    week_13 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 13"))
    week_14 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 14"))
    week_15 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 15"))
    week_16 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 16"))
    week_17 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 17"))
    week_18 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 18"))
    week_19 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 19"))
    week_20 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 20"))
    week_21 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 21"))
    week_22 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 22"))
    week_23 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 23"))
    week_24 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 24"))
    week_25 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 25"))
    week_26 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 26"))
    week_27 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 27"))
    week_28 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 28"))
    week_29 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 29"))
    week_30 = forms.DecimalField(max_value=100, min_value=0, required=False, label=_("Week 30"))

    def clean(self):
        total = Decimal(0)
        cleaned = self.cleaned_data
        outputs = dict()

        for i in range(1,31):
            key = 'week_%d' % i
            if key in cleaned and not cleaned[key] is None:
                total += cleaned[key]
                outputs[key] = cleaned[key]
            else:
                break

        # total not 100%, that's a problem
        if total != Decimal('100'):
            raise forms.ValidationError(_("Total of the outputs must equal 100%"))

        return outputs

    class Meta:
        model = Assumptions

class AssumptionsCRUDL(SmartCRUDL):
    model = Assumptions
    actions = ('read', 'update', 'change', 'output')

    class Output(SmartUpdateView):
        form_class = OutputForm
        fields = ('week_1', 'week_2', 'week_3', 'week_4', 'week_5', 'week_6', 'week_7', 'week_8', 'week_9', 'week_10',
                  'week_11', 'week_12', 'week_13', 'week_14', 'week_15', 'week_16', 'week_17', 'week_18', 'week_19', 'week_20',
                  'week_21', 'week_22', 'week_23', 'week_24', 'week_25', 'week_26', 'week_27', 'week_28', 'week_29', 'week_30')
        success_url = 'id@dashboard.assumptions_update'
        success_message = _("Output curve updated.")

        def post_save(self, obj, *args, **kwargs):
            obj = super(AssumptionsCRUDL.Output, self).post_save(obj, *args, **kwargs)

            # remove all existing output curves
            PredictedOutput.objects.filter(season=self.object.season).delete()

            # write our new ones
            week = 1
            slug = 'week_%d' % week
            cleaned = self.form.cleaned_data

            while slug in cleaned:
                PredictedOutput.objects.create(season=self.object.season, week=week, percentage=cleaned[slug],
                                               created_by=self.request.user, modified_by=self.request.user)
                week += 1
                slug = 'week_%d' % week
                
            return obj

        def derive_initial(self, *args, **kwargs):
            initial = super(AssumptionsCRUDL.Output, self).derive_initial(*args, **kwargs)

            # look up existing outputs
            outputs = PredictedOutput.objects.filter(season=self.object.season)
            for output in outputs:
                initial['week_%d' % output.week] = output.percentage

            return initial

    class Update(SmartUpdateView):
        readonly = ('season', 'csp', 'wetmill')
        exclude = ('is_active', 'created_by', 'modified_by')
        success_message = _("Wetmill settings have been updated.")

        def derive_title(self):
            if self.object.wetmill:
                return _("Edit Wetmill Settings")
            else:
                return _("Edit Global Settings")

        def get_context_data(self, **kwargs):
            context = super(AssumptionsCRUDL.Update, self).get_context_data(**kwargs)

            # if our assumption is on a wetmill, get the csp defaults (or season defaults)
            season_defaults = Assumptions.get_or_create(season=self.object.season, csp=None, wetmill=None, user=self.request.user)
            default_assumptions = season_defaults
            if self.object.wetmill and not self.object.csp:
                csp = self.object.wetmill.get_csp_for_season(self.object.season)
                if csp:
                    default_assumptions = Assumptions.get_or_create(season=self.object.season, csp=csp, wetmill=None, user=self.request.user)
                    default_assumptions.set_defaults(season_defaults)

            defaults = dict()

            if self.object.wetmill or self.object.csp:
                for field in Assumptions.DEFAULT_FIELDS:
                    value = getattr(default_assumptions, field)
                    if not value is None:
                        defaults[field] = value

            context['price_transition'] = Assumptions.PRICE_FIELDS[0]
            context['alert_transition'] = Assumptions.ALERT_FIELDS[0]

            context['defaults'] = defaults
            return context

        def customize_form_field(self, name, field):
            if not self.object.wetmill and not self.object.csp and name in Assumptions.DEFAULT_FIELDS:
                field.required = True

            return field

        def get_success_url(self, *args, **kwargs):
            if self.object.wetmill:
                return reverse('dashboard.wetmill_wetmill', args=[self.object.wetmill.id]) + "?season=%d" % self.object.season.pk
            else:
                return reverse('dashboard.wetmill_dashboard') + "?season=%d" % self.object.season.pk

        def has_permission(self, request, *args, **kwargs):
            assumptions = Assumptions.objects.get(pk=kwargs['pk'])
            return Assumptions.can_edit(assumptions.season, assumptions.csp, assumptions.wetmill, request.user)

        def derive_fields(self, *args, **kwargs):
            fields = ['target', 'cherry_parchment_ratio', 'parchment_green_ratio', 'parchment_value',
                      'green_price_differential', 'season_start', 'season_end', ]

            if not self.object.csp and not self.object.wetmill:
                return ['season'] + fields + ['washing_station_costs', 'milling_costs', 'working_capital_costs', 'capex_costs', 'fi_costs', 'total_working_capital',
                                              'total_wetmill_profit', 'total_farmer_distribution_amount', 'total_yearly_reinvestment_amount', 'wetmill_second_price'] + Assumptions.ALERT_FIELDS
            elif not self.object.wetmill:
                return ['season', 'csp'] + fields + ['washing_station_costs', 'milling_costs', 'working_capital_costs', 'capex_costs', 'fi_costs', 'total_working_capital',
                                                     'total_wetmill_profit', 'total_farmer_distribution_amount', 'total_yearly_reinvestment_amount', 'wetmill_second_price'] + Assumptions.ALERT_FIELDS
            else:
                return ['season', 'wetmill'] + fields + ['washing_station_costs', 'milling_costs', 'working_capital_costs', 'capex_costs', 'fi_costs', 'total_working_capital',
                                                         'total_wetmill_profit', 'total_farmer_distribution_amount', 'total_yearly_reinvestment_amount', 'wetmill_second_price'] + Assumptions.ALERT_FIELDS

    class Change(SmartTemplateView):

        def has_permission(self, *args, **kwargs):
            super(AssumptionsCRUDL.Change, self).has_permission(*args,  **kwargs)
            return True

        def pre_process(self, *args, **kwargs):
            super(AssumptionsCRUDL.Change, self).pre_process(*args,  **kwargs)

            season_id = self.request.REQUEST.get('season', None)
            season = Season.objects.get(pk=season_id)

            csp_id = self.request.REQUEST.get('csp', None)
            csp = None
            if csp_id:
                csp = CSP.objects.get(pk=csp_id)

            wetmill_id = self.request.REQUEST.get('wetmill', None)
            wetmill = None
            if wetmill_id:
                wetmill = Wetmill.objects.get(pk=wetmill_id)

            if Assumptions.can_edit(season, csp, wetmill, self.request.user):
                # get or create our assumptions
                assumptions = Assumptions.get_or_create(season, csp, wetmill, self.request.user)

                # ok, let's redirect the user to that edit page
                return HttpResponseRedirect(reverse('dashboard.assumptions_update', args=[assumptions.id]))
            else:
                return HttpResponseRedirect(reverse('users.user_login'))
