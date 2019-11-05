from smartmin.views import *
from .models import *
from .pdf.render import PDFScorecard
from standards.models import StandardCategory, Standard

from perms.models import has_wetmill_permission
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

class StandardForm(ModelForm):
    class Meta:
        model = Standard

    def clean(self):
        cleaned_data = super(StandardForm, self).clean()

        if self.instance.is_finalized:
            empty_field_ids = []
            season_standards = self.instance.season.standards.all()

            for (key, value) in cleaned_data.items():
                if key.startswith('standard__') and value is None or value == '-1':
                    item_id = int(key[10:]) 
                    empty_field_ids.append(item_id)
                    
            if len(empty_field_ids) > 0:
                empty_fields = [standard.name for standard in season_standards if standard.id in sorted(empty_field_ids)]
                message = _("Unable to amend scorecard because the following fields are missing:  ")
                raise ValidationError(message + ", ".join(empty_fields))

        return cleaned_data
                    

class ScorecardCRUDL(SmartCRUDL):
    actions = ('read', 'update', 'list', 'lookup', 'standards', 'pdf', 'finalize')
    model = Scorecard
    permissions = True

    class List(SmartListView):
        fields = ('wetmill', 'season', 'season.country', 'is_finalized')
        search_fields = ('wetmill__name__icontains', 'season__country__name__icontains')
        default_order = ('season__country__name', 'season__name', 'wetmill__name')

        def has_permission(self, request, *args, **kwargs):
            from perms.models import has_any_permission
            return has_any_permission(request.user, 'scorecard_edit') or request.user.has_perm('scorecards.scorecard_list')

        def derive_queryset(self, **kwargs):
            queryset = super(ScorecardCRUDL.List, self).derive_queryset(**kwargs)
            from perms.models import get_all_wetmills_with_permission

            if not self.request.user.has_perm('scorecards.scorecard_list'):
                # build up a list of all the wetmills we have a permission
                wetmills = get_all_wetmills_with_permission(self.request.user, 'scorecard_edit')
                return queryset.filter(wetmill__in=wetmills)
            else:
                return queryset

    class Pdf(SmartReadView):
        
        def render_to_response(self, context, **kwargs):
            try:
                from cStringIO import StringIO
            except ImportError: # pragma: no cover
                from StringIO import StringIO

            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=%s.pdf' % self.object.wetmill.name.lower()

            output_buffer = StringIO()
            scorecard = PDFScorecard(self.object)
            scorecard.render(output_buffer)

            response.write(output_buffer.getvalue())
            output_buffer.close()

            return response

        def has_permission(self, request, *args, **kwargs):
            """
            Overloaded to check the user's permission on wetmill level
            """
            wetmill = Scorecard.objects.get(pk=kwargs['pk']).wetmill
            permissions = ["report_edit", "report_view"]

            has_perm = False
            for permission in permissions:
                has_perm = has_wetmill_permission(request.user, wetmill, permission)
                if has_perm:
                    return has_perm

            return has_perm

    class Read(SmartReadView):

        def derive_title(self):
            return "%s %s" % (self.object.wetmill.name, self.object.season.name)

        def has_permission(self, request, *args, **kwargs):
            from perms.models import has_wetmill_permission
            scorecard = self.get_object()
            return has_wetmill_permission(request.user, scorecard.wetmill, 'scorecard_edit', season=scorecard.season)

        def get_context_data(self, *args, **kwargs):
            context_data = super(ScorecardCRUDL.Read, self).get_context_data(*args, **kwargs)
            context_data['attribute_fields'] = ('client_id', 'auditor', 'audit_date')

            season_category_ids = [standard.category.id for standard in self.object.season.standards.all()]
            context_data['standard_categories'] = StandardCategory.objects.filter(id__in=season_category_ids)

            season_standards = self.object.season.standards.all()
            for standard in season_standards:
                entry = self.object.standard_entries.filter(standard=standard)
                if entry:
                    standard.scorecard_value = entry[0].value
                else:
                    standard.scorecard_value = None
            context_data['season_standards'] = season_standards

            if self.object.is_finalized:
                context_data['edit_button'] = "Amend"
            else:
                context_data['edit_button'] = "Edit"

            languages = []
            languages.append(dict(name="English", language_code="en_us"))
            context_data['languages'] = languages
            context_data['amendments'] = self.object.amendments.all()

            return context_data

    class Lookup(SmartReadView):
        permission = None

        @classmethod
        def derive_url_pattern(cls, path, action):
            """
            Overloaded to return a URL pattern that takes both a wetmill id and season id
            """
            return r'^%s/%s/(?P<wetmill>\d+)/(?P<season>\d+)/$' % (path, action)

        def has_permission(self, request, *args, **kwargs):
            return True

        def pre_process(self, request, *args, **kwargs):
            """
            Overloaded to load a scorecard from a wetmill and season
            """
            wetmill = Wetmill.objects.get(pk=kwargs['wetmill'])
            season = Season.objects.get(pk=kwargs['season'])

            if has_wetmill_permission(request.user, wetmill, "scorecard_edit"):
                # get or create the scorecard for this wetmill in this season
                scorecard = Scorecard.get_for_wetmill_season(wetmill, season, request.user)
                return HttpResponseRedirect(reverse('scorecards.scorecard_read', args=[scorecard.id]))

            elif has_wetmill_permission(request.user, wetmill, "scorecard_view"):
                # can view the existing reports which are finalized
                existing = Scorecard.objects.filter(wetmill=wetmill, season=season, is_finalized=True)

                if existing:
                    return HttpResponseRedirect(reverse('scorecards.scorecard_read', args=[existing[0].id]))
                else:
                    return HttpResponseRedirect(reverse('users.user_login'))
            else:
                return HttpResponseRedirect(reverse('users.user_login'))

    class Standards(SmartUpdateView):
        fields = ('client_id', 'auditor', 'audit_date')
        success_url = 'id@scorecards.scorecard_read'
        form_class = StandardForm

        def has_permission(self, request, *args, **kwargs):
            from perms.models import has_wetmill_permission
            scorecard = self.get_object()
            return has_wetmill_permission(request.user, scorecard.wetmill, 'scorecard_edit', season=scorecard.season)

        def derive_title(self):
            return "%s - %s" % (self.object.wetmill.name, self.object.season.name)

        def get_form(self, form_class):
            form = super(ScorecardCRUDL.Standards, self).get_form(form_class)

            self.standard_fields = []

            # add the fields from scorecard
            for field in self.fields:
                form.fields.insert(len(form.fields), field, forms.CharField(required=False))

            season_standards = self.object.season.standards.all()

            VALUE_NONE = -1
            VALUE_FAIL = 0
            VALUE_PASS = 100

            MR_CHOICES = ((VALUE_NONE, ''),
                          (VALUE_FAIL, 'Fail'),
                          (VALUE_PASS, 'Pass'))

            for standard in season_standards:
                field_name = 'standard__%d' % standard.id
                standard_config = dict(field=field_name, standard=standard)

                standard_field = forms.IntegerField(label=standard.name, required=False,
                                                    help_text="The value of %s during this season" % standard.name.lower())

                if standard.kind == 'MR':
                    standard_field = forms.ChoiceField(label=standard.name, choices=MR_CHOICES, required=False,
                                                       help_text="The value of %s during this season" % standard.name.lower())
                elif standard.kind == 'BP':
                    standard_field = forms.IntegerField(label=standard.name, max_value=100, min_value=0, required=False,
                                                        help_text="The value of %s during this season" % standard.name.lower())

                form.fields.insert(len(form.fields), field_name, standard_field)

                self.standard_fields.append(standard_config)

            return form

        def get_context_data(self, *args, **kwargs):
            context_data = super(ScorecardCRUDL.Standards, self).get_context_data(*args, **kwargs)
            context_data['attribute_fields'] = ('client_id', 'auditor', 'audit_date')
            context_data['standard_fields'] = self.standard_fields
            season_category_ids = [standard.category.id for standard in self.object.season.standards.all()]
            context_data['standard_categories'] = StandardCategory.objects.filter(id__in=season_category_ids)

            return context_data

        def save_m2m(self, *args, **kwargs):
            super(ScorecardCRUDL.Standards, self).save_m2m(*args, **kwargs)

            # clear out existing values
            self.object.standard_entries.all().delete()

            clean = self.form.cleaned_data

            for standard_field in self.standard_fields:
                value_field = standard_field['field']
                standard = standard_field['standard']

                if value_field in clean and not clean[value_field] is None:
                    if int(clean[value_field]) >= 0:
                        self.object.standard_entries.create(standard=standard, value=clean[value_field],
                                                            created_by=self.request.user, modified_by=self.request.user)

            # after save amended standards make sure to re-finalize if the scorcard was finalized before
            if self.object.is_finalized and len(self.form.changed_data) > 1:
                self.object.save()
                self.object.finalize()

                fields_status = []
                amended_standards = [standard for standard in self.standard_fields if standard['field'] in self.form.changed_data]
                amend = self.object.amendments.create(created_by=self.request.user, modified_by=self.request.user)

                description = ""

                if 'audit_date' in self.form.changed_data:
                    description += ", Audit Date from %s to %s" % (self.form.initial['audit_date'], clean['audit_date'])
                    
                if 'auditor' in self.form.changed_data:
                    description += ", Auditor from %s to %s" % (self.form.initial['auditor'], clean['auditor'])

                for amended in amended_standards:
                    name = amended['standard'].name
                    old = self.form.initial[amended['field']]
                    new = self.form.clean()[amended['field']]
                    description += ", %s from %s to %s" % (name, old, new)

                amend.description = "Modified by %s on %s - Changed%s" % (amend.modified_by ,amend.created_on.strftime("%b %d %Y %H:%M:%S"), description)
                amend.save()

        def derive_initial(self, *args, **kwargs):
            initial = super(ScorecardCRUDL.Standards, self).derive_initial(*args, **kwargs)

            for entry in self.object.standard_entries.all():
                initial['standard__%d' % entry.standard.id] = entry.value

            return initial

    class Finalize(SmartUpdateView):
        success_url = 'id@scorecards.scorecard_read'
        fields = ('is_finalized',)

        def has_permission(self, request, *args, **kwargs):
            from perms.models import has_wetmill_permission
            scorecard = self.get_object()
            return has_wetmill_permission(request.user, scorecard.wetmill, 'scorecard_edit', season=scorecard.season)

        def form_valid(self, form):
            try:
                self.object.save()
                self.object.finalize()
                messages.success(self.request, _("Your Scorecard has been finalized"))
                return HttpResponseRedirect(self.get_success_url())
            except ScorecardFinalizeException as empty_fields:
                messages.error(self.request, empty_fields.message)
                return HttpResponseRedirect(self.get_success_url())
