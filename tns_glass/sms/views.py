from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from tns_glass.dashboard.models import Assumptions
from wetmills.models import Wetmill, WetmillCSPSeason
from csps.models import CSP
from sms.models import Accountant, CSPOfficer, CPO, WetmillObserver
from .models import *
from django.core.paginator import *
from rapidsms.models import Connection
from django.contrib import messages
from seasons.models import Season
from perms.models import *
from smartmin.views import *
from django.utils.translation import ugettext_lazy as _

class GetWetmillMixin(object): # pragma: no cover
    def get_wetmill(self):
        return Wetmill.objects.get(pk=self.request.REQUEST['wetmill'])

    def get_context_data(self, **kwargs):
        context = super(GetWetmillMixin, self).get_context_data(**kwargs)
        context['wetmill'] = self.get_wetmill()
        return context

class CheckViewPermission(object): # pragma: no cover

    def has_permission(self, request, *args, **kwargs):
        wetmill = Wetmill.objects.get(pk=request.REQUEST['wetmill'])
        return has_wetmill_permission(request.user, wetmill, 'sms_view')

class CheckEditPermission(object): # pragma: no cover

    def has_permission(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        wetmill = self.lookup_wetmill(request)
        return has_wetmill_permission(request.user, wetmill, 'sms_edit')

class SubmissionListView(CheckViewPermission, GetWetmillMixin, SmartListView):
    template_name = 'sms/submission_list.html'

    def get_submitted(self, obj):
        if obj.submission:
            return obj.submission.created
        else:
            return obj.created_by

    def get_queryset(self, **kwargs):
        season = self.request.GET['season']
        return self.model.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-report_day', '-active')

    def get_context_data(self, **kwargs):
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        context['season'] = Season.objects.get(pk=self.request.GET.get('season'))
        return context

class SubmissionDeleteView(CheckEditPermission, SmartUpdateView):
    fields = ('active',)
    submit_button_name = "Yes"
    template_name = "sms/submission_delete.html"

    def lookup_wetmill(self, request):
        return self.get_object().wetmill

    def pre_save(self, obj):
        obj = super(SubmissionDeleteView, self).pre_save(obj)
        obj.active = False
        obj.is_active = False

        return obj

    def get_success_url(self):
        return reverse('dashboard.wetmill_wetmill', args=[self.object.wetmill.pk]) + "?season=%d" % self.object.season.pk

class DailySubmissionCreateView(CheckEditPermission, SmartCreateView):
    readonly = ('wetmill', 'season', 'report_day')
    template_name = 'sms/submission_create.html'

    def get_context_data(self, **kwargs):
        context = super(DailySubmissionCreateView, self).get_context_data(**kwargs)
        context['template'] = self.get_template()
        context['wetmill'] = self.get_wetmill(None)
        context['season'] = self.get_season(None)
        context['day'] = self.get_report_day(None)

        if context['template'] and context['template'].active:
            context['delete_url'] = self.get_delete_url(context['template'])

        return context

    def pre_save(self, obj):
        obj = super(DailySubmissionCreateView, self).pre_save(obj)

        obj.wetmill = self.get_wetmill(obj)
        obj.season = self.get_season(obj)
        obj.report_day = datetime.strptime(self.get_report_day(obj), "%B %d, %Y").date()

        obj.active = True
        obj.is_active = True

        return obj

    def get_template(self):
        template = self.request.REQUEST.get('template', None)
        if template:
            return self.model.all.get(pk=template)
        else:
            return None

    def get_wetmill(self, obj):
        template = self.get_template()
        if template:
            return template.wetmill
        else:
            return Wetmill.objects.get(pk=self.request.REQUEST['wetmill'])

    def get_season(self, obj):
        template = self.get_template()
        if template:
            return template.season
        else:
            return Season.objects.get(pk=self.request.REQUEST['season'])

    def get_report_day(self, obj):
        template = self.get_template()
        if template:
            return template.report_day.strftime("%B %d, %Y")
        else:
            return self.request.REQUEST['report_day']

    def get_success_url(self):
        return reverse('dashboard.wetmill_wetmill', args=[self.object.wetmill.pk]) + "?season=%d" % self.object.season.pk

    def lookup_wetmill(self, request):
        self.request = request
        return self.get_wetmill(None)

    def get_weight(self):
        season = self.get_season(None)
        return season.country.weight


class WeeklySubmissionCreateView(DailySubmissionCreateView):
    readonly = ('wetmill', 'season', 'start_of_week')
    template_name = 'sms/submission_create.html'

    def get_context_data(self, **kwargs):
        context = super(DailySubmissionCreateView, self).get_context_data(**kwargs)
        context['template'] = self.get_template()
        context['wetmill'] = self.get_wetmill(None)
        context['season'] = self.get_season(None)
        context['day'] = self.get_start_of_week(None)

        if context['template'] and context['template'].active:
            context['delete_url'] = self.get_delete_url(context['template'])

        return context

    def pre_save(self, obj):
        obj = super(DailySubmissionCreateView, self).pre_save(obj)

        obj.wetmill = self.get_wetmill(obj)
        obj.season = self.get_season(obj)
        obj.start_of_week = datetime.strptime(self.get_start_of_week(obj), "%B %d, %Y").date()

        obj.active = True
        obj.is_active = True

        return obj

    def get_start_of_week(self, obj):
        template = self.get_template()
        if template:
            return template.start_of_week.strftime("%B %d, %Y")
        else:
            return self.request.REQUEST['start_of_week']

class AmafarangaCRUDL(SmartCRUDL): # pragma: no cover
    model = AmafarangaSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Cash submission deleted.")

    class List(SubmissionListView):
        fields = ('start_of_week', 'opening_balance', 'working_capital', 'other_income', 'full_time_labor',
                  'advanced', 'casual_labor', 'commission', 'transport', 'other_expenses', 'submitted')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.amafarangasubmission_create') + "?template=%d" % obj.pk, obj.start_of_week)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return AmafarangaSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-start_of_week', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'start_of_week', 'opening_balance', 'working_capital', 'other_income', 'advanced', 'full_time_labor',
                  'casual_labor', 'commission', 'transport', 'other_expenses')
        readonly = ('wetmill', 'season', 'start_of_week')
        title = _("Cash Submission")
        success_message = _("Cash submission created.")

        def get_delete_url(self, template):
            return reverse('sms.amafarangasubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                return dict(opening_balance=template.opening_balance,
                            working_capital=template.working_capital,
                            other_income=template.other_income,
                            advanced=template.advanced,
                            full_time_labor=template.full_time_labor,
                            casual_labor=template.casual_labor,
                            commission=template.commission,
                            transport=template.transport,
                            other_expenses=template.other_expenses)
            else:
                return super(AmafarangaCRUDL.Create, self).derive_initial()

class SitokiCRUDL(SmartCRUDL): # pragma: no cover
    model = SitokiSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Stock submission deleted.")

    class List(SubmissionListView):
        fields = ('start_of_week', 'grade_a_stored', 'grade_b_stored', 'grade_c_stored',
                  'grade_a_shipped', 'grade_b_shipped', 'grade_c_shipped', 'submitted')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.sitokisubmission_create') + "?template=%d" % obj.pk, obj.start_of_week)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return SitokiSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-start_of_week', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'start_of_week', 'grade_a_stored', 'grade_b_stored', 'grade_c_stored',
                  'grade_a_shipped', 'grade_b_shipped', 'grade_c_shipped')
        readonly = ('wetmill', 'season', 'start_of_week')
        title = _("Stock Submission")
        success_message = _("Stock submission created.")

        def get_delete_url(self, template):
            return reverse('sms.sitokisubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                country = template.season.country

                grade_a_stored=to_country_weight(template.grade_a_stored, country)
                grade_b_stored=to_country_weight(template.grade_b_stored, country)
                grade_c_stored=to_country_weight(template.grade_c_stored, country)
                grade_a_shipped=to_country_weight(template.grade_a_shipped, country)
                grade_b_shipped=to_country_weight(template.grade_b_shipped, country)
                grade_c_shipped=to_country_weight(template.grade_c_shipped,country)

                return dict(grade_a_stored=grade_a_stored,
                            grade_b_stored=grade_b_stored,
                            grade_c_stored=grade_c_stored,
                            grade_a_shipped=grade_a_shipped,
                            grade_b_shipped=grade_b_shipped,
                            grade_c_shipped=grade_c_shipped)
            else:
                return super(SitokiCRUDL.Create, self).derive_initial()

        def get_form(self, form_class):
            self.form = super(SitokiCRUDL.Create, self).get_form(form_class)

            self.form.fields['grade_a_stored'].help_text = self.form.fields['grade_a_stored'].help_text + " (in " + self.get_weight().name + ")"
            self.form.fields['grade_b_stored'].help_text = self.form.fields['grade_b_stored'].help_text + " (in " + self.get_weight().name + ")"
            self.form.fields['grade_c_stored'].help_text = self.form.fields['grade_c_stored'].help_text + " (in " + self.get_weight().name + ")"
            self.form.fields['grade_a_shipped'].help_text = self.form.fields['grade_a_shipped'].help_text + " (in " + self.get_weight().name + ")"
            self.form.fields['grade_b_shipped'].help_text = self.form.fields['grade_b_shipped'].help_text + " (in " + self.get_weight().name + ")"
            self.form.fields['grade_c_shipped'].help_text = self.form.fields['grade_c_shipped'].help_text + " (in " + self.get_weight().name + ")"

            return self.form

        def pre_save(self, obj):
            obj = super(SitokiCRUDL.Create, self).pre_save(obj)

            weight_ratio = self.get_weight().ratio_to_kilogram

            obj.grade_a_stored = self.form.cleaned_data['grade_a_stored'] * weight_ratio
            obj.grade_b_stored = self.form.cleaned_data['grade_b_stored'] * weight_ratio
            obj.grade_c_stored = self.form.cleaned_data['grade_c_stored'] * weight_ratio
            obj.grade_a_shipped = self.form.cleaned_data['grade_a_shipped'] * weight_ratio
            obj.grade_b_shipped = self.form.cleaned_data['grade_b_shipped'] * weight_ratio
            obj.grade_c_shipped = self.form.cleaned_data['grade_c_shipped'] * weight_ratio

            return obj

class IbitumbweCRUDL(SmartCRUDL): # pragma: no cover
    model = IbitumbweSubmission
    actions = ('create', 'list', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Ibitumbwe submission deleted.")

    class List(SubmissionListView):
        fields = ('report_day', 'cash_advanced', 'cash_returned', 'cash_spent', 'credit_spent', 'cherry_purchased', 'submitted')

        def get_report_day(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.ibitumbwesubmission_create') + "?template=%d" % obj.pk, obj.report_day)

    class Create(DailySubmissionCreateView):
        fields = ('wetmill', 'season', 'report_day', 'cash_advanced', 'cash_returned', 'cash_spent', 'credit_spent', 'cherry_purchased')
        readonly = ('wetmill', 'season', 'report_day')
        title = _("Daily Submission")
        success_message = _("Daily submission created.")

        def get_delete_url(self, template):
            return reverse('sms.ibitumbwesubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()

            if template:
                cherry_purchased = to_country_weight(template.cherry_purchased, template.season.country)

                return dict(cash_advanced=template.cash_advanced,
                            cash_returned=template.cash_returned,
                            cash_spent=template.cash_spent,
                            credit_spent=template.credit_spent,
                            cherry_purchased=cherry_purchased)
            else:
                return super(IbitumbweCRUDL.Create, self).derive_initial()

        def get_form(self, form_class):
            self.form = super(IbitumbweCRUDL.Create, self).get_form(form_class)

            self.form.fields['cherry_purchased'].help_text = self.form.fields['cherry_purchased'].help_text + " (in " + self.get_weight().name + ")"

            return self.form

        def pre_save(self, obj):
            obj = super(IbitumbweCRUDL.Create, self).pre_save(obj)

            weight_ratio = self.get_weight().ratio_to_kilogram

            obj.cherry_purchased = self.form.cleaned_data['cherry_purchased'] * weight_ratio

            return obj


class TwakinzeCRUDL(SmartCRUDL): # pragma: no cover
    model = TwakinzeSubmission
    actions = ('create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Closed submission removed.")

    class Create(DailySubmissionCreateView):
        fields = ('wetmill', 'season', 'report_day')
        readonly = ('wetmill', 'season', 'report_day')
        success_message = "Wetmill Marked as Closed."

        def get_delete_url(self, template):
            return reverse('sms.twakinzesubmission_delete', args=[template.pk])

class IgurishaCRUDL(SmartCRUDL): # pragma: no cover
    model = IgurishaSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Sales submission deleted.")

    class List(SubmissionListView):
        fields = ('sales_date', 'grade', 'volume', 'price',
                  'currency', 'exchange_rate', 'sale_type')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.igurishasubmission_create') + "?template=%d" % obj.pk, obj.sales_date)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return IgurishaSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-sales_date', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'sales_date', 'grade', 'volume', 'price',
                  'currency', 'exchange_rate', 'sale_type')
        readonly = ('wetmill', 'season', 'sales_date')
        title = _("Green Sales Submission")
        success_message = _("Green Sales Submission created.")

        def get_delete_url(self, template):
            return reverse('sms.igurishasubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                country = template.season.country

                grade=to_country_weight(template.grade, country)

                return dict(grade=grade)
            else:
                return super(IgurishaCRUDL.Create, self).derive_initial()

        def get_form(self, form_class):
            self.form = super(IgurishaCRUDL.Create, self).get_form(form_class)

            self.form.fields['grade'].help_text = " (in " + self.get_weight().name + ")"
            return self.form

        def pre_save(self, obj):
            obj = super(IgurishaCRUDL.Create, self).pre_save(obj)

            weight_ratio = self.get_weight().ratio_to_kilogram

            obj.grade = self.form.cleaned_data['grade'] * weight_ratio
            
            return obj


    model = IgurishaSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Cash submission deleted.")

    class List(SubmissionListView):
        fields = ('start_of_week', 'opening_balance', 'working_capital', 'other_income', 'full_time_labor',
                  'advanced', 'casual_labor', 'commission', 'transport', 'other_expenses', 'submitted')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.igurishasubmission_create') + "?template=%d" % obj.pk, obj.start_of_week)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return IgurishaSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-start_of_week', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'start_of_week', 'opening_balance', 'working_capital', 'other_income', 'advanced', 'full_time_labor',
                  'casual_labor', 'commission', 'transport', 'other_expenses')
        readonly = ('wetmill', 'season', 'start_of_week')
        title = _("Cash Submission")
        success_message = _("Cash submission created.")

        def get_delete_url(self, template):
            return reverse('sms.igurishasubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                return dict(opening_balance=template.opening_balance,
                            working_capital=template.working_capital,
                            other_income=template.other_income,
                            advanced=template.advanced,
                            full_time_labor=template.full_time_labor,
                            casual_labor=template.casual_labor,
                            commission=template.commission,
                            transport=template.transport,
                            other_expenses=template.other_expenses)
            else:
                return super(IgurishaSubmission.Create, self).derive_initial()

class DepanseCRUDL(SmartCRUDL): # pragma: no cover
    model = DepanseSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Sales submission deleted.")

    class List(SubmissionListView):
        fields = ('sales_date', 'grade', 'volume', 'price',
                  'currency', 'exchange_rate', 'sale_type')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.depansesubmission_create') + "?template=%d" % obj.pk, obj.sales_date)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return DepanseSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-sales_date', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'sales_date', 'grade', 'volume', 'price',
                  'currency', 'exchange_rate', 'sale_type')
        readonly = ('wetmill', 'season', 'sales_date')
        title = _("Green Sales Submission")
        success_message = _("Green Sales Submission created.")

        def get_delete_url(self, template):
            return reverse('sms.depansesubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                country = template.season.country

                grade=to_country_weight(template.grade, country)

                return dict(grade=grade)
            else:
                return super(DepanseCRUDL.Create, self).derive_initial()

        def get_form(self, form_class):
            self.form = super(DepanseRUDL.Create, self).get_form(form_class)

            self.form.fields['grade'].help_text = self.form.fields['grade_a_stored'].help_text + " (in " + self.get_weight().name + ")"
            return self.form

        def pre_save(self, obj):
            obj = super(DepanseRUDL.Create, self).pre_save(obj)

            weight_ratio = self.get_weight().ratio_to_kilogram

            obj.grade = self.form.cleaned_data['grade'] * weight_ratio
            
            return obj


    model = DepanseSubmission
    actions = ('list', 'create', 'delete')

    class Delete(SubmissionDeleteView):
        success_message = _("Cash submission deleted.")

    class List(SubmissionListView):
        fields = ('start_of_week', 'opening_balance', 'working_capital', 'other_income', 'full_time_labor',
                  'advanced', 'casual_labor', 'commission', 'transport', 'other_expenses', 'submitted')

        def get_start_of_week(self, obj):
            return '<a href="%s">%s</a>' % (reverse('sms.depansesubmission_create') + "?template=%d" % obj.pk, obj.start_of_week)

        def get_queryset(self, **kwargs):
            season = self.request.GET['season']
            return DepanseSubmission.all.filter(wetmill=self.get_wetmill(), season=season).order_by('-start_of_week', '-active')

    class Create(WeeklySubmissionCreateView):
        fields = ('wetmill', 'season', 'start_of_week', 'opening_balance', 'working_capital', 'other_income', 'advanced', 'full_time_labor',
                  'casual_labor', 'commission', 'transport', 'other_expenses')
        readonly = ('wetmill', 'season', 'start_of_week')
        title = _("Cash Submission")
        success_message = _("Cash submission created.")

        def get_delete_url(self, template):
            return reverse('sms.depansesubmission_delete', args=[template.pk])

        def derive_initial(self):
            template = self.get_template()
            if template:
                return dict(opening_balance=template.opening_balance,
                            working_capital=template.working_capital,
                            other_income=template.other_income,
                            advanced=template.advanced,
                            full_time_labor=template.full_time_labor,
                            casual_labor=template.casual_labor,
                            commission=template.commission,
                            transport=template.transport,
                            other_expenses=template.other_expenses)
            else:
                return super(DepanseSubmission.Create, self).derive_initial()

def gather_season_stats(wetmills, season): # pragma: no cover
    # for each wetmill we have to gather the aggregate statistics for this season
    totals = dict(a_shipped=Decimal(0), b_shipped=Decimal(0), c_shipped=Decimal(0),
                  a_stored=Decimal(0), b_stored=Decimal(0), c_stored=Decimal(0),
                  parchment=Decimal(0), cherry=Decimal(0), spent=Decimal(0),
                  price=Decimal(0), ratio=Decimal(0))

    for wetmill in wetmills:
        stats = dict()
        
        parchment = SitokiSubmission.objects.filter(wetmill=wetmill, season=season).aggregate(
            Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'), 
            Sum('grade_a_shipped'), Sum('grade_b_shipped'), Sum('grade_c_shipped')).order_by('-start_of_week')

        stats['a_shipped'] = parchment['grade_a_shipped__sum'] or Decimal(0)
        stats['b_shipped'] = parchment['grade_b_shipped__sum'] or Decimal(0)
        stats['c_shipped'] = parchment['grade_c_shipped__sum'] or Decimal(0)
        stats['a_stored'] = parchment['grade_a_stored__sum'] or Decimal(0)
        stats['b_stored'] = parchment['grade_b_stored__sum'] or Decimal(0)
        stats['c_stored'] = parchment['grade_c_stored__sum'] or Decimal(0)

        cherry = IbitumbweSubmission.objects.filter(wetmill=wetmill, season=season).aggregate(
            Sum('cherry_purchased'), Sum('cash_spent'), Sum('credit_spent'))

        stats['parchment'] = stats['a_stored'] + stats['b_stored'] + stats['c_stored']
        stats['cherry'] = cherry['cherry_purchased__sum'] or Decimal(0)
        if stats['parchment']:
            stats['ratio'] = stats['cherry'] / stats['parchment']
        else:
            stats['ratio'] = Decimal(0)
        stats['spent'] = (cherry['cash_spent__sum'] or Decimal(0)) + (cherry['credit_spent__sum'] or Decimal(0))

        if stats['spent']:
            stats['price'] = stats['spent'] / stats['cherry']
        else:
            stats['price'] = Decimal(0)

        for key in stats:
            totals[key] += stats[key]

        wetmill.stats = stats

    # fix up our totals
    if totals['spent']:
        totals['price'] = totals['cherry'] / totals['spent']
    else:
        totals['price'] = Decimal(0)

    if totals['parchment']:
        totals['ratio'] = totals['cherry'] / totals['parchment']
    else:
        totals['ratio'] = Decimal(0)

    return totals

def sms_view(request, wetmill_id, season_id=None): # pragma: no cover
    from dashboard.models import Assumptions

    wetmill = Wetmill.objects.get(pk=wetmill_id)
    season_id = request.REQUEST.get('season', season_id)

    if season_id is None:
        season = Season.objects.filter(country__name='Rwanda')[0]
    else:
        season = Season.objects.get(pk=season_id)

    if not has_wetmill_permission(request.user, wetmill, 'sms_view'):
        return HttpResponseRedirect(reverse('users.user_login'))

    seasons = Season.objects.filter(country=wetmill.country)
    context = dict(wetmill=wetmill, season=season, country=wetmill.country, currency=wetmill.country.currency, seasons=seasons)
    context['can_edit_assumptions'] = Assumptions.can_edit(season, wetmill.get_csp_for_season(season), wetmill, request.user)
    context['accounting_system'] = wetmill.get_accounting_for_season(season)

    add_sms_data_to_context(request, context, wetmill, season)
    return render_to_response('sms/sms_view.html', context, context_instance = RequestContext(request))

def sms_clear(request, wetmill_id, season_id): # pragma: no cover
    wetmill = Wetmill.objects.get(pk=wetmill_id)
    season = Season.objects.get(pk=season_id)

    if not has_wetmill_permission(request.user, wetmill, 'sms_edit'):
        return HttpResponseRedirect(reverse('users.user_login'))

    if request.method == 'POST':
        for msg in AmafarangaSubmission.objects.filter(wetmill=wetmill, season=season):
            msg.active = False
            msg.is_active = False
            msg.save()

        for msg in IbitumbweSubmission.objects.filter(wetmill=wetmill, season=season):
            msg.active = False
            msg.is_active = False
            msg.save()

        for msg in SitokiSubmission.objects.filter(wetmill=wetmill, season=season):
            msg.active = False
            msg.is_active = False
            msg.save()

        for msg in TwakinzeSubmission.objects.filter(wetmill=wetmill, season=season):
            msg.active = False
            msg.is_active = False
            msg.save()
            
        messages.success(request, _("Messages cleared for %s wetmill") % wetmill.name)

    return HttpResponseRedirect(reverse('dashboard.wetmill_wetmill', args=[wetmill_id]) + "?season=%s" % season_id)

def sms_disassociate(request, wetmill_id, actor_id): # pragma: no cover
    wetmill = Wetmill.objects.get(pk=wetmill_id)
    actor = Actor.objects.get(pk=actor_id)

    if not has_wetmill_permission(request.user, wetmill, 'sms_edit'):
        return HttpResponseRedirect(reverse('users.user_login'))

    if request.method == 'POST':
        actor.active = False    
        actor.save()

        messages.success(request, _("%s removed from wetmill") % actor.name)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def to_dec(val): # pragma: no cover
    if isinstance(val, Decimal):
        return val
    else:
        return Decimal(val.replace(',', ''))

def add_sms_data_to_context(request, context, wetmill, season): # pragma: no cover
    accounting_system = wetmill.get_accounting_for_season(season)

    if accounting_system == '2012':
        # group them up by day to make the template easier
        grouped_by_day = []

        submission_types = [
            ('amafaranga', list(AmafarangaSubmission.objects.filter(season=season, wetmill=wetmill).select_related(depth=1).order_by('-start_of_week')), []),
            ('ibitumbwe', list(IbitumbweSubmission.objects.filter(season=season, wetmill=wetmill).select_related(depth=1).order_by('-report_day')), []),
            ('sitoki', list(SitokiSubmission.objects.filter(season=season, wetmill=wetmill).select_related(depth=1).order_by('-start_of_week')), []),
            ('twakinze', list(TwakinzeSubmission.objects.filter(season=season, wetmill=wetmill).select_related(depth=1).order_by('-report_day')), []),
            ('igurisha', list(IgurishaSubmission.objects.filter(season=season, wetmill=wetmill).select_related(depth=1).order_by('-report_day')), []),
        ]

        # calculate our totals
        for (sub_type, subs, totals) in submission_types:
            for sub in subs:
                data = sub.get_data()
                while len(totals) < len(data):
                    totals.append(None)

                for (index, d) in enumerate(data):
                    if d.get('total', False):
                        if totals[index]:
                            totals[index] += to_dec(d['value'])
                        else:
                            totals[index] = to_dec(d['value'])
                    else:
                        totals[index] = None

    elif accounting_system == 'FULL':
        # get aggregate values for our submission types so we can table them
        cherry_report = CherrySubmission.objects.filter(season=season, wetmill=wetmill).values('daylot').order_by('-created').annotate(
            Sum('cherry'), Sum('cherry_paid_credit'), Sum('cherry_paid_cash'))

        store_report = StoreSubmission.objects.filter(season=season, wetmill=wetmill).values('daylot').order_by('-created').annotate(
            Sum('gradea_moved'), Sum('gradeb_moved'))

        shipping_report = ShippingSubmission.objects.filter(season=season, wetmill=wetmill).values('day').order_by('-created').annotate(
            Sum('parchmenta_kg'), Sum('parchmenta_bags'), Sum('parchmentb_kg'), Sum('parchmentb_bags'))

        # group them up by day to make the template easier
        grouped_by_day = []
        for report in cherry_report:
            grouped_by_day.append({ 'day':datetime_for_daylot(report['daylot']), 'cherry':report})

        for report in cherry_report:
            for day in grouped_by_day:
                if day['day'] == datetime_for_daylot(report['daylot']):
                    if report['cherry__sum']:
                        day['average'] = (report['cherry_paid_credit__sum'] + report['cherry_paid_cash__sum']) / report['cherry__sum']
                    else:
                        day['average'] = Decimal(0)

        for report in store_report:
            for day in grouped_by_day:
                if day['day'] == datetime_for_daylot(report['daylot']):
                    day['store'] = report

        for report in shipping_report:
            for day in grouped_by_day:
                if day['day'] == report['day']:
                    day['shipping'] = report

        submission_types = [
            ('cherry', CherrySubmission.objects.filter(wetmill=wetmill, season=season).select_related(depth=1).order_by('-created')[:10]),
            ('store', StoreSubmission.objects.filter(wetmill=wetmill, season=season).select_related(depth=1).order_by('-created')[:10]),
            ('shipping', ShippingSubmission.objects.filter(wetmill=wetmill, season=season).select_related(depth=1).order_by('-created')[:10]),
            ('cash', CashSubmission.objects.filter(wetmill=wetmill, season=season).select_related(depth=1).order_by('-created')[:10]),
        ]
    elif accounting_system == 'LITE':
        # get values, grouped by day
        summary_report = SummarySubmission.objects.filter(wetmill=wetmill, season=season).values('day').order_by('-created').annotate(
            Sum('cherry'), Sum('paid'), Sum('stored'), Sum('sent'), Avg('balance'))

        # group them up by day to make the template easier
        grouped_by_day = []
        for report in summary_report:
            grouped_by_day.append({ 'day':report['day'], 'summary':report})
        
        submission_types = [
            ('summary', SummarySubmission.objects.filter(wetmill=wetmill, season=season).select_related(depth=1).order_by('-created')[:10]),
        ]


    if accounting_system == 'NONE':
        grouped_by_day = []
        submission_types = []
        accountant = None
        observers = []
        cpos = []
    else:
        context['observers'] = WetmillObserver.objects.filter(wetmill=wetmill)
        context['cpos'] = CPO.objects.filter(wetmill=wetmill)
        try:
            context['accountant'] = Accountant.objects.get(wetmill=wetmill)
        except Accountant.DoesNotExist:
            pass

    context['can_edit'] = has_wetmill_permission(request.user, wetmill, 'sms_edit')

    context['submissions_by_day'] = grouped_by_day
    context['submission_types'] = submission_types

    context['wetmill'] = wetmill
    context['season'] = season

def build_context(actor, request): # pragma: no cover
    context = dict()

    try:
        actor.firstname = actor.name.lower().title().split(' ')[0]
        actor.lastname = actor.name.lower().title().split(' ')[1]
    except IndexError:
        actor.firstname = actor.name.lower().title().split(' ')[0]

    actor.number = actor.connection.identity[2:]

    paginator = Paginator(actor.connection.messages.all().order_by('-date'), 20)
    page = request.GET.get('page')

    try:
        actor.messages = paginator.page(page)
    except EmptyPage:
        actor.messages = paginator.page(paginator.num_pages)
    except:
        actor.messages = paginator.page(1)

    context['paginator'] = paginator

    return context        

def submission_actor(request, identity, actor_id=None): # pragma: no cover
    """
    Check who is associated with a phone number and displays all submissions related to them
    """
    context = None

    try:
        accountant = Accountant.objects.get(connection__identity=identity)
        
        context = build_context(accountant, request)
        accountant.title = _("Accountant")
        accountant.cash = accountant.cashsubmission_set.all()
        accountant.cherry = accountant.cherrysubmission_set.all()
        accountant.returned = accountant.returnsubmission_set.all()
        accountant.shipping = accountant.shippingsubmission_set.all()
        accountant.store = accountant.storesubmission_set.all()
        accountant.summary = accountant.summarysubmission_set.all()
        context['accountant'] = accountant

    except Accountant.DoesNotExist:
        pass

    try:
        cspofficer = CSPOfficer.objects.get(connection__identity=identity)

        context = build_context(cspofficer, request)
        cspofficer.title = _("CSP Officer")
        cspofficer.received = cspofficer.receivedsubmission_set.all()

        context['cspofficer'] = cspofficer

    except CSPOfficer.DoesNotExist:
        pass

    cpos = CPO.objects.filter(connection__identity=identity)

    if cpos:
        cpo = cpos[0]

        if actor_id:
            cpo = CPO.objects.get(connection__identity=identity, cpo_id=actor_id)

        cpos = CPO.objects.filter(connection__identity=identity).exclude(cpo_id=cpo.cpo_id)
        
        context = build_context(cpo, request)
        cpo.title = _("Site Collector Officer")
        cpo.cherry = cpo.cherrysubmission_set.all()
        cpo.returned = cpo.returnsubmission_set.all()

        context['cpo'] = cpo
        context['cpos'] = cpos

    observers = WetmillObserver.objects.filter(connection__identity=identity)
    
    if observers:
        observer = observers[0]

        if actor_id:
            observer = WetmillObserver.objects.get(connection__identity=identity, id=actor_id)

        observers = WetmillObserver.objects.filter(connection__identity=identity).exclude(id=observer.id)

        context = build_context(observer, request)
        observer.title = _("Wetmill Observer")

        context['observer'] = observer
        context['observers'] = observers

    if context == None:

        context = dict()
        # display messages for unregistered user
        unregistered = Connection.objects.get(identity=identity)
        
        unregistered.firstname, unregistered.lastname = ("Unregistered", "User")
        unregistered.title = _("Unknown")
        unregistered.number = unregistered.identity[2:]
        paginator = Paginator(unregistered.messages.all(), 20)
        page = request.GET.get('page')

        try:
            messages = paginator.page(page)
        except EmptyPage:
            messages = paginator.page(paginator.num_pages)
        except:
            messages = paginator.page(1)

        context['unregistered'] = unregistered
        context['messages'] = messages

    return render_to_response('router/actor.html',
                              context,
                              context_instance = RequestContext(request))

