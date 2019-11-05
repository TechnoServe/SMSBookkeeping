from .models import FinalizeTask
from smartmin.views import *
from django.utils.translation import ugettext_lazy as _

class FinalizeTaskCRUDL(SmartCRUDL):
    model = FinalizeTask
    actions = ('create', 'list', 'read', 'finalize')
    permissions = True

    class List(SmartListView):
        fields = ('status', 'season', 'created_by')

        def get_status(self, obj):
            return obj.get_status()

    class Read(SmartReadView):

        def derive_title(self):
            return _("Finalize %s Season") % (self.object.season.name)

        def derive_refresh(self):
            if self.object.get_status() == 'STARTED' or self.object.get_status() == 'PENDING':
                return 2000
            else: # pragma: no cover
                return 0

    class Finalize(SmartReadView):
        def pre_process(self, request, *args, **kwargs):
            try:
                self.get_object().start()
            except Exception as e: # pragma: no cover
                task = self.get_object()
                task.log("Couldn't queue finalize, contact administrator.")
            return HttpResponseRedirect(reverse('aggregates.finalizetask_read', args=[self.get_object().pk]))

    class Create(SmartCreateView):
        title = _("Finalize Season")
        success_url = "id@aggregates.finalizetask_finalize"
        fields = ('season',)
        submit_button_name = _("Finalize")

