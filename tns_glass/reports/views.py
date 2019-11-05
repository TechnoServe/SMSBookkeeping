from smartmin.views import *
from .models import *
from wetmills.models import Wetmill, WetmillCSPSeason, WetmillSeasonAccountingSystem
from seasons.models import Season
from public.models import get_report_currencies, get_report_weights
from locales.models import Currency, Weight
from perms.models import has_wetmill_permission, has_country_permission, get_wetmills_with_permission
from django.http import HttpResponse
from .pdf.render import PDFReport
from django.http import HttpResponseRedirect
from util.fields import TreeModelChoiceField
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

def log_amendment(view):
    changes = []

    for changed in view.form.changed_data:
        if changed != 'loc':
            name = view.form.fields[changed].label
            old = view.form.initial[changed]
            new = view.form.clean()[changed]
            changes.append("%s from %s to %s" % (name, str(old), str(new)))

    description = "Changed %s" % (", ".join(changes))
    return view.object.amendments.create(description=description, created_by=view.request.user, modified_by=view.request.user)

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report

    def clean(self):
        cleaned_data = super(ReportForm, self).clean()

        empty_fields = []
        if self.instance.is_finalized and len(self.changed_data) > 0:
            for field in self.changed_data:
                if self.cleaned_data[field] is None:
                    empty_fields.append(self.fields[field].label)

        if empty_fields:
            message = _("Unable to amend transparency report because the following fields are missing: ")
            raise ValidationError(message + ", ".join(empty_fields))

        return cleaned_data


class ReportCRUDL(SmartCRUDL):
    actions = ('create', 'read', 'update', 'list', 'lookup', 'attributes', 'production', 'expenses', 'pdf', 'finalize')
    model = Report
    permissions = True

    class Create(SmartCreateView):
        fields = ('season', 'wetmill')
        template_name = 'reports/report_create.html'


        def get_allowed_seasons(self):
            allowed_seasons = []

            seasons = [_['season'] for _ in WetmillSeasonAccountingSystem.objects.all().exclude(accounting_system='NONE').values('season').distinct()]
            for season in Season.objects.filter(id__in=seasons):
                print 'Season object=' + str(season)
                wetmills = get_wetmills_with_permission(self.request.user, season, 'sms_view')
                if wetmills:
                    season.wetmills = wetmills
                    allowed_seasons.append(season)

            return allowed_seasons

        def get_context_data(self, *args, **kwargs):
            context = super(ReportCRUDL.Create, self).get_context_data(*args, **kwargs)

            context['seasons'] = self.get_allowed_seasons()

            season = self.request.POST.get('season')
            wetmill = self.request.POST.get('wetmill')

            if season == -1:
                season = None

            if wetmill == -1:
                wetmill = None

            if season and not wetmill:
                context['season'] = long(season)  # Converted to long because we are going to compare it with the selected season in the template which is a long value.
                season_object = Season.objects.get(id=season)
                print 'Selected Season=' + str(season) + ' What that means=' + str(season_object)
                wetmills = get_wetmills_with_permission(self.request.user, season_object, 'sms_view')
                context['wetmills'] = wetmills

            elif season and wetmill:
                # Now save data
                # Does the report already exist?
                report_entry = Report.get_for_wetmill_season(wetmill, season, self.request.user)

                if report_entry:
                    #url_value = reverse('reports.report_list') + '?report_mode=CR'
                    #url_value = '/reports/report/create/?report_mode=CR'
                    #return HttpResponseRedirect(url_value)
                    context["creation_message"] = "Credit Report Saved."

            return context


    class List(SmartListView):
        search_fields = ('wetmill__name__icontains', 'wetmill__country__name__icontains', 'season__name__icontains')
        fields = ('wetmill', 'season', 'season.country', 'is_finalized')
        default_order = ('season__country__name', 'season__name', 'wetmill__name')
        link_fields = ('wetmill',)
        paginate_by = 50

        # We want to modify the link so that it contains the get parameter with the report mode.
        def lookup_field_link(self, context, field, obj):
            report_mode = self.request.REQUEST.get('report_mode', 'CR')
            context['report_mode'] = report_mode
            return '/reports/report/read/' + str(obj.id) + '?report_mode=' + report_mode

        def get_is_finalized(self, obj):
            if obj.is_finalized:
                return "Yes"
            else:
                return "No"

    class Pdf(SmartReadView):

        def render_to_response(self, context, **kwargs):
            from django.utils.translation import activate

            currency_code = self.request.REQUEST.get('currency', 'USD')
            currency = Currency.objects.get(currency_code=currency_code)

            weight_abbreviation = self.request.REQUEST.get('weight', 'Kg')
            weight = Weight.objects.get(abbreviation__iexact=weight_abbreviation)

            try:
                from cStringIO import StringIO
            except ImportError: # pragma: no cover
                from StringIO import StringIO

            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=%s_%s.pdf' % (self.object.wetmill.name.lower(), 
                                                                                  currency.currency_code.lower())

            show_buyers = has_wetmill_permission(self.request.user, self.object.wetmill, 'report_edit')

            # activate our local
            activate(self.request.REQUEST.get('lang', 'en_us'))

            output_buffer = StringIO()

            pdf_report = PDFReport(self.object, currency, weight, report_mode=self.request.REQUEST.get('report_mode', 'CR'),
                                   show_buyers=show_buyers)
            pdf_report.render(output_buffer)

            response.write(output_buffer.getvalue())
            output_buffer.close()

            # back to english
            activate('en_us')

            return response

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            permissions = ["report_edit", "report_view"]

            has_perm = False
            for permission in permissions:
                has_perm = has_wetmill_permission(request.user, wetmill, permission)
                if has_perm:
                    return has_perm

            return has_perm

    class Read(SmartReadView):
        def get_context_data(self, *args, **kwargs):
            context = super(ReportCRUDL.Read, self).get_context_data(*args, **kwargs)

            context['cherry_production'] = self.object.production_for_kind('CHE')

            wetmill_production = self.object.production_for_season_grades('PAR')
            wetmill_production += self.object.production_for_season_grades('GRE')
            context['wetmill_production'] = wetmill_production

            expenses = self.object.entries_for_season_expenses()
            halfway = len(expenses) / 2
            while (halfway >= 0 and len(expenses) > 0):
                if expenses[halfway]['expense'].depth == 0:
                    break
                halfway -= 1

            context['wetmill_expenses'] = expenses
            context['halfway_point'] = halfway
            context['dollars'] = Currency.objects.get(currency_code='USD')

            context['cashuses'] = self.object.cash_uses_for_season()
            context['cashsources'] = self.object.cash_sources_for_season()
            context['payments'] = self.object.farmer_payments_for_season()

            context['sales'] = self.object.sales.all()

            if self.object.is_finalized:
                context['edit_button'] = "Amend"
            else:
                context['edit_button'] = "Edit"

            # build our list of currencies for the report
            country = self.object.season.country
            currencies = get_report_currencies(country, "USD")
            context['currencies'] = currencies

            if country.weight != Weight.objects.get(abbreviation__iexact="Kg"):
                context['weights'] = get_report_weights(country, 'Kg')

            languages = []
            languages.append(dict(name="English", language_code="en_us"))
            languages.append(dict(name=country.get_language_display(), language_code=country.language))
            context['languages'] = languages
            context['amendments'] = self.object.amendments.all()

            return context

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            permissions = ["report_edit", "report_view"]

            has_perm = False
            for permission in permissions:
                has_perm = has_wetmill_permission(request.user, wetmill, permission)
                if has_perm:
                    return has_perm

            return has_perm

    class Lookup(SmartReadView):
        permission = None

        def has_permission(self, request, *args, **kwargs):
            return True

        @classmethod
        def derive_url_pattern(cls, path, action):
            """
            Overloaded to return a URL pattern that takes both a wetmill id and season id
            """
            return r'^%s/%s/(?P<wetmill>\d+)/(?P<season>\d+)/$' % (path, action)

        def pre_process(self, request, *args, **kwargs):
            """
            Overloaded to load a report from a wetmill and season
            """
            wetmill = Wetmill.objects.get(pk=kwargs['wetmill'])
            season = Season.objects.get(pk=kwargs['season'])

            if has_wetmill_permission(request.user, wetmill, "report_edit"):
                # get or create the report for this wetmill in this season
                report = Report.get_for_wetmill_season(wetmill, season, request.user)
                return HttpResponseRedirect(reverse('reports.report_read', args=[report.id]))

            elif has_wetmill_permission(request.user, wetmill, "report_view"):
                # Can view the existing reports which are finalized
                existing = Report.objects.filter(wetmill=wetmill, season=season, is_finalized=True)

                if existing:
                    return HttpResponseRedirect(reverse('reports.report_read', args=[existing[0].id]))
                else:
                    return HttpResponseRedirect(reverse('users.user_login'))
            else:
                return HttpResponseRedirect(reverse('users.user_login'))

    class Attributes(SmartUpdateView):
        fields = ('working_capital', 'working_capital_repaid', 'miscellaneous_revenue')
        success_url = 'id@reports.report_read'
        form_class = ReportForm

        def derive_title(self):
            return "%s - %s" % (self.object.wetmill.name, self.object.season.name)

        def get_form(self, form_class):
            form = super(ReportCRUDL.Attributes, self).get_form(form_class)

            curr = self.object.season.country.currency.currency_code

            self.cashsource_fields = []
            for cashsource in self.object.season.get_cash_sources().filter(calculated_from='NONE'):
                field_name = 'cashsource__%d' % cashsource.id
                field = forms.DecimalField(label=_("%s Total") % cashsource.name, required=False,
                                           help_text=_("The total amount distributed as a %s, in the local currency") % cashsource.name)
                form.fields.insert(len(form.fields), field_name, field)

                cashsource.field = field_name
                self.cashsource_fields.append(cashsource)

            self.cashuse_fields = []
            for cashuse in self.object.season.get_cash_uses().filter(calculated_from='NONE'):
                field_name = 'cashuse__%d' % cashuse.id
                field = forms.DecimalField(label=_("%s Total") % cashuse.name, required=False,
                                           help_text=_("The total amount spent on the %s, in the local currency") % cashuse.name)
                form.fields.insert(len(form.fields), field_name, field)

                cashuse.field = field_name
                self.cashuse_fields.append(cashuse)

            self.payment_fields = []
            for payment in self.object.season.get_farmer_payments():
                field_map = {}
                fields = []

                if payment.applies_to == 'ALL':
                    field_name = 'payment__%d__all_kil' % payment.id
                    field = forms.DecimalField(label=_("%s per Kilo") % payment.name, required=False,
                                               help_text=_("The amount distributed to farmers as a %s per kilo of cherry, in the local currency") % payment.name)
                    form.fields.insert(len(form.fields), field_name, field)
                    fields.append(dict(name=field_name, unit="%s / Kg Cherry" % curr))
                    field_map['all_per_kilo'] = fields[-1]

                if payment.applies_to == 'MEM' or payment.applies_to == 'BOT':
                    field_name = 'payment__%d__mem_kil' % payment.id
                    field = forms.DecimalField(label=_("Member %s per Kilo") % payment.name, required=False,
                                               help_text=_("The amount distributed to members as a %s per kilo of cherry, in the local currency") % payment.name)
                    form.fields.insert(len(form.fields), field_name, field)
                    fields.append(dict(name=field_name, unit="%s / Kg Cherry" % curr))
                    field_map['member_per_kilo'] = fields[-1]

                if payment.applies_to == 'NON' or payment.applies_to == 'BOT':
                    field_name = 'payment__%d__non_kil' % payment.id
                    field = forms.DecimalField(label=_("Non-Member %s per Kilo") % payment.name, required=False,
                                               help_text=_("The amount distributed to non-members as a %s per kilo of cherry, in the local currency") % payment.name)
                    form.fields.insert(len(form.fields), field_name, field)
                    fields.append(dict(name=field_name, unit="%s / Kg Cherry" % curr))
                    field_map['non_member_per_kilo'] = fields[-1]

                payment.fields = fields
                payment.field_map = field_map
                self.payment_fields.append(payment)

            return form

        def derive_initial(self, *args, **kwargs):
            initial = super(ReportCRUDL.Attributes, self).derive_initial(*args, **kwargs)

            for entry in self.object.cash_uses.all():
                initial['cashuse__%d' % entry.cash_use.id] = entry.value

            for entry in self.object.cash_sources.all():
                initial['cashsource__%d' % entry.cash_source.id] = entry.value

            for entry in self.object.farmer_payments.all():
                if not entry.all_per_kilo is None:
                    initial['payment__%d__all_kil' % entry.farmer_payment.id] = entry.all_per_kilo

                if not entry.member_per_kilo is None:
                    initial['payment__%d__mem_kil' % entry.farmer_payment.id] = entry.member_per_kilo

                if not entry.non_member_per_kilo is None:
                    initial['payment__%d__non_kil' % entry.farmer_payment.id] = entry.non_member_per_kilo

            return initial

        def post_save(self, obj):
            obj = super(ReportCRUDL.Attributes, self).post_save(obj)

            if obj.is_finalized:
                obj.calculate_metrics()
                obj.save()

            return obj

        def save_m2m(self):
            super(ReportCRUDL.Attributes, self).save_m2m()

            self.object.cash_uses.all().delete()
            self.object.cash_sources.all().delete()
            self.object.farmer_payments.all().delete()

            clean = self.form.cleaned_data

            for cashuse in self.cashuse_fields:
                if not clean.get(cashuse.field, None) is None:
                    self.object.cash_uses.create(cash_use=cashuse,
                                                 value=clean[cashuse.field],
                                                 created_by=self.request.user,
                                                 modified_by=self.request.user)

            for cashsource in self.cashsource_fields:
                if not clean.get(cashsource.field, None) is None:
                    self.object.cash_sources.create(cash_source=cashsource,
                                                    value=clean[cashsource.field],
                                                    created_by=self.request.user,
                                                    modified_by=self.request.user)

            for payment in self.payment_fields:
                fields = payment.field_map
                kwargs = dict()

                for key in fields:
                    kwargs[key] = clean[fields[key]['name']]

                # if there is at least one value
                if kwargs:
                    self.object.farmer_payments.create(farmer_payment=payment,
                                                       created_by=self.request.user,
                                                       modified_by=self.request.user,
                                                       **kwargs)

            if self.object.is_finalized and len(self.form.changed_data) > 0:
                log_amendment(self)

        def get_context_data(self, *args, **kwargs):
            context = super(ReportCRUDL.Attributes, self).get_context_data(*args, **kwargs)
            context['cashuse_fields'] = self.cashuse_fields
            context['cashsource_fields'] = self.cashsource_fields
            context['payment_fields'] = self.payment_fields
            return context

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

    class Expenses(SmartUpdateView):
        success_url = 'id@reports.report_read'
        form_class = ReportForm

        def derive_title(self):
            return "%s - %s" % (self.object.wetmill.name, self.object.season.name)

        def get_form(self, form_class):
            form = super(ReportCRUDL.Expenses, self).get_form(form_class)
            form.fields.clear()

            self.expense_fields = []
            season_expenses = self.object.entries_for_season_expenses()
            for season_expense in season_expenses:
                expense = season_expense['expense']
                field_name = 'expense__%d' % expense.id

                expense_config = dict(field=field_name, expense=expense)

                if not expense.is_parent:
                    expense_field = forms.DecimalField(label=expense.name, required=False,
                                                       help_text=_("The amount spent on %s during this season") %
                                                       expense.name.lower())
                    form.fields.insert(len(form.fields), field_name, expense_field)

                    if expense.in_dollars:
                        exchange_field_name = 'expense__exchange__%d' % expense.id
                        exchange_field = forms.DecimalField(label=_("%s Exchange Rate") % expense.name, required=False)
                        form.fields.insert(len(form.fields), exchange_field_name, exchange_field)
                        expense_config['exchange_field'] = exchange_field_name

                self.expense_fields.append(expense_config)

            return form

        def save_m2m(self, *args, **kwargs):
            super(ReportCRUDL.Expenses, self).save_m2m(*args, **kwargs)

            # clear out existing values
            self.object.expenses.all().delete()

            clean = self.form.cleaned_data
            for expense_field in self.expense_fields:
                field = expense_field['field']
                expense = expense_field['expense']

                if field in clean and not clean[field] is None:
                    exchange = None

                    # if this expense is in dollars, see if they entered an exchange rate
                    if expense.in_dollars:
                        exchange_field = expense_field['exchange_field']
                        if exchange_field in clean and not clean[exchange_field] is None:
                            exchange = clean[exchange_field]

                    self.object.expenses.create(expense=expense, value=clean[field], exchange_rate=exchange,
                                                created_by=self.request.user, modified_by=self.request.user)

            if self.object.is_finalized and len(self.form.changed_data) > 0:
                log_amendment(self)

        def post_save(self, obj):
            obj = super(ReportCRUDL.Expenses, self).post_save(obj)

            if obj.is_finalized:
                obj.calculate_metrics()
                obj.save()

            return obj

        def get_context_data(self, *args, **kwargs):
            context = super(ReportCRUDL.Expenses, self).get_context_data(*args, **kwargs)
            context['expense_fields'] = self.expense_fields

            return context

        def derive_initial(self, *args, **kwargs):
            initial = super(ReportCRUDL.Expenses, self).derive_initial(*args, **kwargs)

            for entry in self.object.expenses.all():
                initial['expense__%d' % entry.expense.id] = entry.value
                if not entry.exchange_rate is None:
                    initial['expense__exchange__%d' % entry.expense.id] = entry.exchange_rate

            return initial

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

    class Production(SmartUpdateView):
        fields = ('farmers', 'capacity', 'cherry_production_by_members')
        success_url = 'id@reports.report_read'
        form_class = ReportForm

        def derive_title(self):
            return "%s - %s" % (self.object.wetmill.name, self.object.season.name)

        def get_form(self, form_class):
            form = super(ReportCRUDL.Production, self).get_form(form_class)

            self.parent_grades = []
            parent_grade = None

            self.grade_fields = []
            for grade in self.object.season.get_grade_tree():
                if grade.depth == 0:
                    parent_grade = grade
                    parent_grade.fields = []
                    self.parent_grades.append(parent_grade)

                if not grade.is_parent:
                    field_name = 'production__%d' % grade.id
                    self.grade_fields.append(dict(field=field_name, grade=grade))
                    grade_field = forms.DecimalField(label=grade.name, required=False,
                                                     help_text=_("The amount of %s collected this season, in kilos") % grade.name.lower())
                    form.fields.insert(len(form.fields), field_name, grade_field)
                    parent_grade.fields.append(field_name)

            return form

        def derive_initial(self, *args, **kwargs):
            initial = super(ReportCRUDL.Production, self).derive_initial(*args, **kwargs)

            for production in self.object.production.all():
                initial['production__%d' % production.grade.id] = production.volume

            return initial

        def save_m2m(self):
            self.object.production.all().delete()

            clean = self.form.cleaned_data
            for grade_field in self.grade_fields:
                field = grade_field['field']
                grade = grade_field['grade']

                if field in clean and not clean[field] is None:
                    self.object.production.create(grade=grade, volume=clean[field],
                                                  created_by=self.request.user, modified_by=self.request.user)

            if self.object.is_finalized and len(self.form.changed_data) > 1:
                log_amendment(self)

        def post_save(self, obj):
            obj = super(ReportCRUDL.Production, self).post_save(obj)

            if obj.is_finalized:
                obj.calculate_metrics()
                obj.save()

            return obj

        def get_context_data(self, *args, **kwargs):
            context = super(ReportCRUDL.Production, self).get_context_data(*args, **kwargs)
            context['grade_fields'] = self.grade_fields
            context['parent_grades'] = self.parent_grades
            return context

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

    class Finalize(SmartUpdateView):
        success_url = 'id@reports.report_read'
        fields = ('is_finalized',)

        def form_valid(self, form):
            try:
                self.object.finalize()
                self.object.save()
                messages.success(self.request, _("Your Report has been finalized"))
                return HttpResponseRedirect(self.get_success_url())
            except ReportFinalizeException as empty_fields:
                messages.error(self.request, str(empty_fields))
                return HttpResponseRedirect(self.get_success_url())

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=kwargs['pk']).wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

class SaleForm(forms.ModelForm):

    def clean(self):
        cleaned = super(SaleForm, self).clean()

        has_component = False
        for i in range(10):
            grade_field = 'component_grade__%d' % i
            volume_field = 'component_volume__%d' % i

            if grade_field in cleaned and not cleaned[grade_field] is None and volume_field in cleaned and cleaned[volume_field]:
                has_component = True

        if not has_component:
            raise forms.ValidationError(_("You must specify at least one grade and volume component for this sale"))

        return cleaned

    def clean_exchange_rate(self):
        cleaned = self.cleaned_data
        exchange_rate = cleaned['exchange_rate']

        # if the sale was in US dollars, they need to enter an exchange rate
        if 'currency' in cleaned and cleaned['currency'].currency_code == 'USD':
            if not exchange_rate:
                raise forms.ValidationError(_("You must specify an exchange rate if the sale was in US dollars"))

        return exchange_rate

    class Meta:
        model = Sale

class SaleCRUDL(SmartCRUDL):
    model = Sale
    actions = ('create', 'update', 'delete')
    permissions = True

    class EditMixin(object):

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Report.objects.get(pk=request.REQUEST['report']).wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

        def get_context_data(self, *args, **kwargs):
            context = super(SaleCRUDL.EditMixin, self).get_context_data(*args, **kwargs)
            context['component_fields'] = self.component_fields

            has_component_errors = False
            for field in self.form.errors:
                if field.find("component_") == 0:
                    has_component_errors = True

            component_count = 1
            if 'component_count' in self.request.REQUEST:
                component_count = int(self.request.REQUEST['component_count'])

            context['component_count'] = component_count

            context['has_component_errors'] = has_component_errors

            return context

        def get_success_url(self, *args, **kwargs):
            return reverse('reports.report_read', args=[self.get_report().id])

        def pre_save(self, obj):
            obj = super(SaleCRUDL.EditMixin, self).pre_save(obj)

            # count the number of component before saving
            self.components_count = len(obj.components.all())

            # clear any adjustment if our sale type is local
            if obj.sale_type == 'LOC':
                obj.adjustment = None

            return obj

        def post_save(self, obj):
            obj = super(SaleCRUDL.EditMixin, self).post_save(obj)

            # if the report is finalized
            if obj.report.is_finalized:
                # in case there is more or less component within a sale, amend!
                if len(obj.components.all()) != self.components_count:
                    description = "%s sale component modified" % self.object.buyer.capitalize()
                    obj.report.amendments.create(description=description, created_by=self.request.user,
                                                 modified_by=self.request.user)

                report = obj.report
                report.calculate_metrics()
                report.save()

            return obj

        def save_m2m(self, *args, **kwargs):
            super(SaleCRUDL.EditMixin, self).save_m2m(*args, **kwargs)

            # clear out existing sale components
            self.object.components.all().delete()

            clean = self.form.cleaned_data
            for component in self.component_fields:
                grade_field = component['grade_field']
                volume_field = component['volume_field']

                # if both the volume and grade have been set
                if grade_field in clean and not clean[grade_field] is None and volume_field in clean and clean[volume_field]:
                    self.object.components.create(grade=clean[grade_field], volume=clean[volume_field],
                                                  created_by=self.request.user, modified_by=self.request.user)

            # start the amendment process if the report has been finalized
            if self.object.report.is_finalized:
                modified = False
                # similar keys in both initial and current data in fields
                keys = [key for key in self.form.initial if key in self.form.cleaned_data.keys()]

                for key in keys:
                    # treat differently the currency cause is stored as an object in clean
                    if key == 'currency':
                        if self.form.initial[key] != self.form.clean()[key].id:
                            modified = True
                            break
                    # then other field
                    else:
                        if self.form.initial[key] != self.form.clean()[key]:
                            modified = True
                            break

                if modified:
                    description = "%s sale modified" % self.object.buyer.capitalize()
                    amend = self.object.report.amendments.create(description=description, created_by=self.request.user, modified_by=self.request.user)

        def get_form(self, *args, **kwargs):
            form = super(SaleCRUDL.EditMixin, self).get_form(*args, **kwargs)
            self.component_fields = []

            form.fields['exchange_rate'].help_text += " (season default is %f)" % self.get_report().season.exchange_rate

            # add 10 component field sets, one each for grade and volume
            for i in range(10):
                grade_field = TreeModelChoiceField(Grade, self.get_report().season.get_grade_tree, required=False)
                volume_field = forms.DecimalField(required=False)

                grade_field_name = 'component_grade__%d' % i
                volume_field_name = 'component_volume__%d' % i

                self.component_fields.append(dict(grade_field=grade_field_name, volume_field=volume_field_name))

                form.fields.insert(len(form.fields), grade_field_name, grade_field)
                form.fields.insert(len(form.fields), volume_field_name, volume_field)


            currency_codes = ['USD', self.get_report().season.country.currency.currency_code]
            form.fields['currency'] = forms.ModelChoiceField(Currency.objects.filter(currency_code__in=currency_codes))

            if self.get_report().season.has_local_sales:
                form.fields['sale_type'] = forms.ChoiceField(Sale.LOCAL_TYPE_CHOICES)
            else:
                form.fields['sale_type'] = forms.ChoiceField(Sale.NO_LOCAL_TYPE_CHOICES)

            return form

    class Create(EditMixin, SmartCreateView):
        fields = ('date', 'buyer', 'price', 'currency', 'exchange_rate', 'sale_type', 'adjustment')
        form_class = SaleForm

        def get_report(self):
            return Report.objects.get(pk=self.request.REQUEST['report'])

        def pre_save(self, obj):
            obj = super(SaleCRUDL.Create, self).pre_save(obj)
            obj.report = self.get_report()

            return obj

        def post_save(self, obj):
            obj = super(SaleCRUDL.EditMixin, self).post_save(obj)

            if self.object.report.is_finalized:
                description = "%s sale added" % obj.buyer.capitalize()
                amend = obj.report.amendments.create(description=description, created_by=self.request.user,
                                                     modified_by=self.request.user)

                report = self.object.report
                report.calculate_metrics()
                report.save()

            return obj

    class Delete(SmartDeleteView):

        def get_cancel_url(self):
            return reverse('reports.report_read', args=[self.object.report.id])

        def get_redirect_url(self):
            return reverse('reports.report_read', args=[self.object.report.id])

        def post(self, request, *args, **kwargs):
            super(SaleCRUDL.Delete, self).post(request, *args, **kwargs)

            if self.object.report.is_finalized:
                description = "%s sale removed" % self.object.buyer.capitalize()
                self.object.report.amendments.create(description=description, created_by=self.request.user,
                                                     modified_by=self.request.user)

                report = self.object.report
                report.calculate_metrics()
                report.save()

            return HttpResponseRedirect(self.get_redirect_url())

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Sale.objects.get(pk=kwargs['pk']).report.wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')

    class Update(EditMixin, SmartUpdateView):
        fields = ('date', 'buyer', 'price', 'currency', 'exchange_rate', 'sale_type', 'adjustment')
        form_class = SaleForm

        def get_report(self):
            return self.object.report

        def derive_initial(self, *args, **kwargs):
            initial = super(SaleCRUDL.Update, self).derive_initial(*args, **kwargs)

            for (index, component) in enumerate(self.object.components.all()):
                initial['component_grade__%d' % index] = component.grade
                initial['component_volume__%d' % index] = component.volume

            return initial

        def get_context_data(self, *args, **kwargs):
            context = super(SaleCRUDL.Update, self).get_context_data(*args, **kwargs)

            context['component_count'] = self.object.components.all().count()
            context['has_more_sale_left'] = len(self.object.report.sales.all()) > 1

            return context

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Sale.objects.get(pk=kwargs['pk']).report.wetmill
            return has_wetmill_permission(request.user, wetmill, 'report_edit')
