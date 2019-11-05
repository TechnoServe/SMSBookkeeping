from smartmin.views import *
from .models import *


class HelpForm(forms.ModelForm):
    message_en_us = forms.CharField(max_length=255, widget=forms.Textarea)
    message_rw = forms.CharField(max_length=255, widget=forms.Textarea)
    message_tz_sw = forms.CharField(max_length=255, widget=forms.Textarea)
    message_am = forms.CharField(max_length=255, widget=forms.Textarea)

    class Meta:
        model = HelpMessage

class HelpCRUDL(SmartCRUDL):
    model = HelpMessage
    actions = ('create', 'update', 'list', 'delete')

    class List(SmartListView):
        fields = ('message', 'reporter_type', 'priority')

    class Update(SmartUpdateView):
        form_class = HelpForm
        success_url = '@xform-list'
        exclude = ('message', 'message_ke_sw')

