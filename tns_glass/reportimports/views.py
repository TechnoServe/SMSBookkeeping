from reports.models import Report
from seasons.models import Season
from smartmin.views import *
from .models import *
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
import csv
from django.utils.translation import ugettext_lazy as _

class ActionForm(forms.Form):
    season = forms.ModelChoiceField(Season.objects.all(),
                                    help_text=_("The season you want a template created for"))
    create = forms.CharField(required=False)
    template = forms.CharField(required=False)

class ReportImportCRUDL(SmartCRUDL):
    model = ReportImport
    actions = ('list', 'read', 'action', 'create', 'import')
    permissions = True

    class List(SmartListView):
        fields = ('season', 'status', 'created_on', 'created_by')

        def get_status(self, obj):
            return obj.get_status()

        def get_context_data(self, *args, **kwargs):
            context = super(ReportImportCRUDL.List, self).get_context_data(*args, **kwargs)
            context['seasons'] = Season.objects.filter(is_active=True)
            return context

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
            return HttpResponseRedirect(reverse('reportimports.reportimport_read', args=[self.get_object().pk]))

    class Create(SmartCreateView):
        title = "Import Season Reports"
        fields = ('season', 'csv_file')
        readonly = ('season',)
        success_url = "id@reportimports.reportimport_import"

        def pre_save(self, obj):
            obj = super(ReportImportCRUDL.Create, self).pre_save(obj)
            obj.season = self.get_season()
            return obj

        def get_season(self, *args):
            return Season.objects.get(id=self.request.REQUEST['season'])

        def get_context_data(self, *args, **kwargs):
            context = super(ReportImportCRUDL.Create, self).get_context_data(*args, **kwargs)
            context['season'] = self.get_season()
            return context

    class Action(SmartFormView):
        template_name = "smartmin/form.html"
        form_class = ActionForm

        def form_valid(self, form):
            clean = form.cleaned_data
            season = clean['season']

            if clean['template']:
                response = HttpResponse(mimetype='application/CSV')
                response['Content-Disposition'] = 'attachment; filename=%s_%s_template.csv' % (season.country.name.lower(), season.name.lower())

                rows = build_sample_rows(season)
                response.write(rows_to_csv(rows))
                return response
            else:
                return HttpResponseRedirect(reverse("reportimports.reportimport_create") + "?season=%s" % season.id)
