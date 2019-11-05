from smartmin.views import *
from .models import *
from django.core.urlresolvers import reverse
from widgets import BoundsField, BoundsWidget
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _

class CountryForm(forms.ModelForm):
    bounds = BoundsField(required=True)

    def clean(self):
        clean = self.cleaned_data

        if 'bounds' in clean:
            self.instance.bounds_lat = clean['bounds']['lat']
            self.instance.bounds_lng = clean['bounds']['lng']
            self.instance.bounds_zoom = clean['bounds']['zoom']        

        return clean

    class Meta:
        model = Country
        fields = ('name', 'country_code', 'language', 'currency', 'weight', 'calling_code', 'phone_format', 'national_id_format')

class PickCountryForm(forms.Form):
    country = forms.ModelChoiceField(Country.objects.all(),
                                help_text=_("Pick the country the new wetmill will be located in"))

class CountryCRUDL(SmartCRUDL):
    model = Country
    actions = ('create', 'list', 'update', 'delete', 'pick')
    permissions = True

    class Pick(SmartFormView):
        form_class = PickCountryForm
        title = _("Pick Wetmill Country")
        submit_button_name = _("Pick Country")

        def get_context_data(self, **kwargs):
            context = super(CountryCRUDL.Pick, self).get_context_data(**kwargs)
            context['next'] = self.request.REQUEST['next']
            return context

        def form_valid(self, form):
            # build up our URL
            url = self.request.REQUEST['next']
            url += "?country=%s" % form.cleaned_data['country'].id
            return HttpResponseRedirect(url)

    class Create(SmartCreateView):
        form_class = CountryForm        
        template_name = 'locales/country_form.html'
        field_config = { 'bounds': dict(label=_("Map Bounds"), help=_("The default map position used for this country, you can set this below.")) }

    class Update(SmartUpdateView):
        form_class = CountryForm
        template_name = 'locales/country_form.html'
        field_config = { 'bounds': dict(label=_("Map Bounds"), help=_("The default map position used for this country, you can set this below.")) }

        def derive_initial(self):
            return dict(bounds=dict(lat=self.object.bounds_lat,
                                    lng=self.object.bounds_lng,
                                    zoom=self.object.bounds_zoom))

    class List(SmartListView):
        fields = ('name', 'country_code', 'currency', 'weight')
        link_fields = ('name', 'currency', 'weight')
        add_button = True

        def lookup_field_link(self, context, field, obj):
            # Link our name and currency fields, each going to their own place
            if field == 'currency':
                return reverse('locales.currency_update', args=[obj.currency.id])
            elif field == 'weight':
                return reverse('locales.weight_update', args=[obj.weight.id])
            else:
                return reverse('locales.country_update', args=[obj.id])

class CurrencyCRUDL(SmartCRUDL):
    model = Currency
    actions = ('create', 'list', 'update')
    permissions = True

    class List(SmartListView):
        template = 'locales/currency.html'
        fields = ('name', 'currency_code', 'format')
        add_button = True        

        def get_format(self, obj):
            val = "3,133"

            if obj.has_decimals:
                val += ".71"

            if not obj.prefix is None:
                val = obj.prefix + val

            if not obj.suffix is None:
                val += obj.suffix

            return val

class WeightCRUDL(SmartCRUDL):
    model = Weight
    actions = ('create', 'list', 'update')

    class List(SmartListView):
        fields = ('name', 'abbreviation', 'ratio_to_kilogram')
        add_button= True

        def get_ratio_to_kilogram(self, obj):
            return "%d Kg" % obj.ratio_to_kilogram


class ProvinceCRUDL(SmartCRUDL):
    model = Province
    actions = ('create', 'list', 'update')
    permissions = True

    class List(SmartListView):
        fields = ('name', 'country', 'order')
        add_button = True
        default_order = ('country__name', 'order')
