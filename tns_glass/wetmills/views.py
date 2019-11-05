from smartmin.views import *
from locales.widgets import *
from locales.models import *
from .models import *
from seasons.models import *
from csps.models import *
import re
from django.utils.translation import ugettext_lazy as _

class WetmillForm(forms.ModelForm):
    coordinates = CoordinatesPickerField(required=True,
                                         help_text=_("The latitude and longitude coordinates of this wetmill.  You can either enter these manually or double click on the map above to set them."))

    accounting_system = forms.ChoiceField(choices=ACCOUNTING_SYSTEM_CHOICES,
                                          help_text=_("What accounting system to use for this wetmill, if any"))

    def clean_coordinates(self):
        coordinates = self.cleaned_data['coordinates']
        if not coordinates:
            raise forms.ValidationError(_("Please set the latitude and longitude coordinates"))

        return coordinates

    def clean(self):
        cleaned = super(WetmillForm, self).clean()
        if 'coordinates' in cleaned:
            self.instance.latitude = cleaned['coordinates']['lat']
            self.instance.longitude = cleaned['coordinates']['lng']

        return cleaned

    class Meta:
        model = Wetmill
        fields = ('is_active', 'country', 'province', 'name', 'sms_name', 'description', 
                  'year_started', 'coordinates', 'altitude', 'accounting_system')

class WetmillCRUDL(SmartCRUDL):
    model = Wetmill
    actions = ('create', 'update', 'list', 'csps', 'accounting')
    permissions = True

    class Create(SmartCreateView):
        form_class = WetmillForm
        template_name = 'wetmills/wetmill_form.html'
        success_url = 'id@wetmills.wetmill_csps'
        fields = ('country', 'province', 'name', 'sms_name', 'description', 'year_started',
                  'coordinates', 'altitude', 'accounting_system')
        readonly = ('country',)

        def derive_initial(self):
            initial_data = super(WetmillCRUDL.Create, self).get_initial()
            initial_data['country'] = self.get_country()
            return initial_data

        def pre_save(self, obj):
            obj = super(WetmillCRUDL.Create, self).pre_save(obj)
            obj.country = self.get_country()
            return obj

        def post_save(self, obj):
            obj = super(WetmillCRUDL.Create, self).post_save(obj)

            # set the accounting system for the last season
            obj.set_accounting_system(self.form.cleaned_data['accounting_system'])
            return obj

        def customize_form_field(self, name, field):
            if name == 'province':
                field.widget.choices.queryset = Province.objects.filter(country=self.get_country())
                return field
            else:
                return super(WetmillCRUDL.Create, self).customize_form_field(name, field)

        def get_country(self, obj=None):
            return Country.objects.get(id=self.request.REQUEST['country'])

        def get_context_data(self, **kwargs):
            context_data = super(WetmillCRUDL.Create, self).get_context_data(**kwargs)
            self.form.fields['coordinates'].set_country(self.get_country())
            return context_data

        def has_permission(self, request, *args, **kwargs):
            self.request = request
            self.kwargs = kwargs

            has_perm = request.user.has_perm(self.permission)
            if not has_perm:
                has_perm = request.user.has_perm('locales.country_wetmill_edit', self.get_country())

            return has_perm

        def get_success_url(self):
            # this user has raw permission to view wetmill lists
            if self.request.user.has_perm('wetmills.wetmill_list'):
                return reverse('wetmills.wetmill_list') + "?country=%d" % self.object.country.id
            else:
                return reverse('public-country', args=[self.object.country.country_code])

    class Update(SmartUpdateView):
        form_class = WetmillForm
        template_name = 'wetmills/wetmill_form.html'
        fields = ('is_active', 'country', 'province', 'name', 'sms_name', 'description', 'year_started', 'coordinates', 'altitude')
        readonly = ('country',)

        def customize_form_field(self, name, field):
            if name == 'province':
                field.widget.choices.queryset = Province.objects.filter(country=self.object.country)
                return field
            else:
                return super(WetmillCRUDL.Update, self).customize_form_field(name, field)

        def derive_initial(self):
            initial = super(WetmillCRUDL.Update, self).derive_initial()
            
            if self.object.latitude and self.object.longitude:
                initial['coordinates'] = dict(lat=self.object.latitude, lng=self.object.longitude)

            return initial

        def get_context_data(self, **kwargs):
            context_data = super(WetmillCRUDL.Update, self).get_context_data(**kwargs)
            self.form.fields['coordinates'].set_country(self.object.country)
            return context_data

        def get_success_url(self):
            # this user has raw permission to view wetmill lists
            if self.request.user.has_perm('wetmills.wetmill_list'):
                return reverse('wetmills.wetmill_list')
            else:
                return reverse('public-wetmill', args=[self.object.pk])

        def has_permission(self, request, *args, **kwargs):
            from perms.models import has_wetmill_permission
            self.request = request
            self.kwargs = kwargs

            has_perm = request.user.has_perm(self.permission)
            if not has_perm:
                has_perm = has_wetmill_permission(request.user, self.get_object(), 'wetmill_edit')

            return has_perm

    class List(SmartListView):
        search_fields = ('name', 'country__name')
        fields = ('name', 'sms_name', 'country')
        default_order = ('country__name', 'name')

        def get_sms_name(self, obj):
            accounting_system = obj.get_accounting_system()
            if accounting_system == '2012' or accounting_system == 'LIT2':
                return '<a href="%s">%s</a>' % (reverse('dashboard.wetmill_wetmill', args=[obj.id]), obj.sms_name)
            else:
                return "%s - %s" % (obj.sms_name, obj.get_accounting_system_display(accounting_system))

    class Accounting(SmartUpdateView):
        success_url = '@wetmills.wetmill_list'
        title = _("Edit Accounting System")

        def get_form(self, form_class):
            form = super(WetmillCRUDL.Accounting, self).get_form(form_class)
            form.fields.clear()

            # for each season, add a model choice field for each CSP for our country
            for season in Season.objects.filter(country=self.object.country):
                accounting_field = forms.ChoiceField(ACCOUNTING_SYSTEM_CHOICES, required=True,
                    label=str(season), help_text=_("The accounting system used in %s") % (season.name))
                field_name = "accounting__%d" % season.id

                form.fields.insert(len(form.fields), field_name, accounting_field)

            return form

        def derive_initial(self):
            initial = super(WetmillCRUDL.Accounting, self).derive_initial()
            for season_accounting in self.object.get_accounting_systems():
                initial['accounting__%d' % season_accounting.season.id] = season_accounting.accounting_system
            return initial

        def save_m2m(self):
            for field in self.form.fields:
                match = re.match('accounting__(\d+)', field)
                if match:
                    season_id = match.group(1)
                    season = Season.objects.get(pk=season_id)
                    self.object.set_accounting_for_season(season, self.form.cleaned_data[field])

    class Csps(SmartUpdateView):
        success_url = '@wetmills.wetmill_list'
        title = _("Edit CSP Assignments")

        def get_form(self, form_class):
            form = super(WetmillCRUDL.Csps, self).get_form(form_class)
            form.fields.clear()

            # for each season, add a model choice field for each CSP for our country
            for season in Season.objects.filter(country=self.object.country):
                csp_field = forms.ModelChoiceField(CSP.objects.filter(country=self.object.country), required=False,
                                                   label=str(season), help_text=_("The CSP that managed this wetmill in %s") % (season.name))
                field_name = "csp__%d" % season.id

                form.fields.insert(len(form.fields), field_name, csp_field)

            return form

        def derive_initial(self):
            initial = super(WetmillCRUDL.Csps, self).derive_initial()
            for season_csp in self.object.get_season_csps():
                initial['csp__%d' % season_csp.season.id] = season_csp.csp.id
            return initial

        def save_m2m(self):
            for field in self.form.fields:
                match = re.match('csp__(\d+)', field)
                if match:
                    season_id = match.group(1)
                    season = Season.objects.get(pk=season_id)
                    self.object.set_csp_for_season(season, self.form.cleaned_data[field])


class WetmillImportCRUDL(SmartCRUDL):
    model = WetmillImport
    actions = ('list', 'read', 'create', 'import')
    permissions = True

    class List(SmartListView):
        fields = ('status', 'country', 'created_by')

        def get_status(self, obj):
            return obj.get_status()

    class Read(SmartReadView):
        def derive_refresh(self):
            if self.object.get_status() == 'STARTED' or self.object.get_status() == 'PENDING':
                return 2000
            else: # pragma: no cover
                return 0

    class Import(SmartReadView):
        def pre_process(self, request, *args, **kwargs):
            try:
                self.get_object().start()
            except Exception as e: # pragma: no cover
                task = self.get_object()
                task.log("Couldn't queue import, contact administrator.")
            return HttpResponseRedirect(reverse('wetmills.wetmillimport_read', args=[self.get_object().pk]))

    class Create(SmartCreateView):
        title = "Import Wetmills"
        success_url = "id@wetmills.wetmillimport_import"
        fields = ('country', 'csv_file')








