from smartmin.views import *
from .models import *
from wetmills.models import Wetmill
from django.utils.translation import ugettext_lazy as _

class WetmillPermissionMixin(object):
    def has_permission(self, request, *args, **kwargs):
        from perms.models import has_wetmill_permission

        if 'wetmill' in request.REQUEST:
            wetmill = Wetmill.objects.get(pk=int(request.REQUEST['wetmill']))
        else:
            self.kwargs = kwargs
            wetmill = self.get_object().wetmill

        has_perm = request.user.has_perm(self.permission)
        if not has_perm:
            has_perm = has_wetmill_permission(request.user, wetmill, 'wetmill_edit')

        return has_perm

class PhotoCRUDL(SmartCRUDL):
    model = Photo
    actions = ('create', 'update', 'list')
    permissions = True

    class Create(WetmillPermissionMixin, SmartCreateView):
        fields = ('is_main', 'caption', 'image')

        def pre_save(self, obj):
            obj = super(PhotoCRUDL.Create, self).pre_save(obj)
            wetmill = Wetmill.objects.get(pk=int(self.request.REQUEST['wetmill']))
            obj.wetmill = wetmill
            return obj

        def form_valid(self, form):
            self.object = form.save(commit=False)

            try:
                self.object = self.pre_save(self.object)
                self.save(self.object)
                self.object = self.post_save(self.object)

                messages.success(self.request, self.derive_success_message())
                return HttpResponseRedirect('%s?wetmill=%d' % (self.get_success_url(), self.object.wetmill.id))

            except IntegrityError as e: # pragma: no cover
                message = str(e).capitalize()
                errors = self.form._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
                errors.append(message)
                return self.render_to_response(self.get_context_data(form=form))

        def derive_exclude(self):
            exclude = super(PhotoCRUDL.Create, self).derive_exclude()
            wetmill = Wetmill.objects.get(pk=int(self.request.REQUEST['wetmill']))

            if len(Photo.objects.filter(is_main=True, wetmill=wetmill)) > 0:
                exclude.append('is_main')

            return exclude

    class Update(WetmillPermissionMixin, SmartUpdateView):
        fields = ('is_active', 'is_main', 'caption', 'image')

        def form_valid(self, form):
            main_photos = [photo for photo in Photo.objects.filter(wetmill=self.object.wetmill) if photo.is_main ]

            if len(main_photos) > 0 and form.cleaned_data['is_main'] == True and form.initial['is_main'] != True:
                message = _("Currently there is an existing Photo for this wetmill which is main")
                errors = self.form._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
                errors.append(message)
                return self.render_to_response(self.get_context_data(form=form))

            self.object = form.save(commit=False)

            try:
                self.object = self.pre_save(self.object)
                self.save(self.object)
                self.object = self.post_save(self.object)

                messages.success(self.request, self.derive_success_message())
                return HttpResponseRedirect('%s?wetmill=%d' % (self.get_success_url(), self.object.wetmill.id))

            except IntegrityError as e: # pragma: no cover
                message = str(e).capitalize()
                errors = self.form._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
                errors.append(message)
                return self.render_to_response(self.get_context_data(form=form))

    class List(WetmillPermissionMixin, SmartListView):
        fields = ('wetmill', 'caption', 'is_main')

        def get_context_data(self, **kwargs):
            context = super(PhotoCRUDL.List, self).get_context_data(**kwargs)
            wetmill = Wetmill.objects.get(pk=int(self.request.REQUEST['wetmill']))
            context['wetmill'] = wetmill
            context['photo_list'] = Photo.objects.filter(wetmill=wetmill)
            context['object_list'] = Photo.objects.filter(wetmill=wetmill)
            return context
