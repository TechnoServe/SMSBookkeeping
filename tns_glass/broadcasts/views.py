from smartmin.views import *
from .models import *
from django_select2 import ModelSelect2MultipleField
from aggregates.models import *
from django.utils.translation import ugettext_lazy as _

class BroadcastForm(forms.ModelForm):
    to_farmers = forms.BooleanField(required=False)
    to_accountants = forms.BooleanField(required=False)
    to_observers = forms.BooleanField(required=False)

    country = forms.ModelChoiceField(Country.objects.filter(is_active=True).order_by('name'), required=True)

    wetmills = ModelSelect2MultipleField(queryset=Wetmill.objects.all(), data_view="wetmills.wetmill_list", required=False)
    csps = ModelSelect2MultipleField(queryset=CSP.objects.all(), data_view="csps.csp_list", required=False)

    exclude_wetmills = ModelSelect2MultipleField(queryset=Wetmill.objects.all(), data_view="wetmills.wetmill_list", required=False,
                                                 help_text=_("Exclude recipients for these wetmills (leave blank for none)"))
    exclude_csps = ModelSelect2MultipleField(queryset=CSP.objects.all(), data_view="csps.csp_list", required=False,
                                             help_text=_("Exclude recipients for these CSPs (leave blank for none)"))

    report_season = forms.ModelChoiceField(Season.objects.filter(is_active=True).order_by('country__name', 'name'), 
                                           required=False)
    sms_season = forms.ModelChoiceField(Season.objects.filter(is_active=True).order_by('country__name', 'name'),
                                        required=False)

    def clean(self):
        cleaned = self.cleaned_data

        if not 'country' in cleaned:
            raise forms.ValidationError(_("You must specify a country for your broadcast"))

        if not cleaned.get('to_farmers', False) and not cleaned.get('to_accountants', False) and not cleaned.get('to_observers', False):
           raise forms.ValidationError(_("You must specify at least one recipient type for your broadcast"))

        if cleaned.get('report_season', None) and cleaned['report_season'].country != cleaned['country']:
            raise forms.ValidationError(_("Your report season must match your country"))

        if cleaned.get('sms_season', None) and cleaned['sms_season'].country != cleaned['country']:
            raise forms.ValidationError(_("Your SMS season must match your country"))

        if cleaned.get('csps', None) and not cleaned.get('sms_season', None) and not cleaned.get('report_season', None): # pragma: no cover
            raise forms.ValidationError(_("You must specify at least one season to filter by CSP"))

        # if no wetmills match this, then blow up
        if cleaned['country'] and not Broadcast.calculate_wetmills(cleaned['country'],
                                                                   cleaned.get('report_season', None), 
                                                                   cleaned.get('sms_season', None),
                                                                   cleaned['wetmills'], cleaned['csps'], 
                                                                   cleaned['exclude_wetmills'], cleaned['exclude_csps']):
            raise forms.ValidationError(_("No wetmills match your criteria, please broaden them and try again"))

        return cleaned

    class Meta:
        model = Broadcast
        fields = ('country', 'to_farmers', 'to_accountants', 'to_observers', 
                  'wetmills', 'csps', 'exclude_wetmills', 'exclude_csps',
                  'report_season', 'sms_season')

class MessageForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs=dict(rows=3)))

    class Meta:
        model = Broadcast
        fields = ('text',)

class ScheduleForm(forms.ModelForm):
    send_date = forms.DateField(help_text=_("On which date this broadcast will be sent (will not send if blank)"), required=False)
    send_time = forms.TimeField(help_text=_("At which time this broadcast will be sent in GMT. (ie: 16:30)"))

    class Meta:
        model = Broadcast
        fields = ('send_date', 'send_time')

class BroadcastCRUDL(SmartCRUDL):
    actions = ('create', 'update', 'read', 'delete', 'list', 'message', 'preview', 'schedule', 'test')
    model = Broadcast

    class Preview(SmartReadView):
        def get_context_data(self, *args, **kwargs):
            context = super(BroadcastCRUDL.Preview, self).get_context_data(*args, **kwargs)

            wetmill = Wetmill.objects.get(pk=self.request.GET['wetmill_id'])
            actor = self.object.get_recipients_for_wetmill(wetmill)

            self.object.text = self.request.GET['text']

            try:
                context['preview'] = self.object.render(wetmill, actor, datetime.now())

                sms_length = len(context['preview'])
                sms_count = (sms_length + 159) / 160
                context['sms_length'] = sms_length
                context['sms_count'] = sms_count

                if not context['preview']:
                    context['preview'] = "** No text, this wetmill would not receive a message **"

            except Exception as e:
                context['preview'] = "** Error: %s **" % str(e)
                context['sms_length'] = 0
                context['sms_count'] = 0

            return context

        def as_json(self, context):
            return dict(preview=context['preview'], sms_length=context['sms_length'], sms_count=context['sms_count'])

    class Test(SmartReadView):
        fields = ('text', 'recipients', 'country', 'report_season', 'sms_season')

        def derive_title(self):
            return "Broadcast Preview"

        def get_recipients(self, obj):
            return obj.get_recipients_display()

        def get_context_data(self, *args, **kwargs):
            context = super(BroadcastCRUDL.Test, self).get_context_data(*args, **kwargs)
            messages = []

            broadcast = self.object
            broadcast.text = self.request.REQUEST.get('text', broadcast.text)

            for wetmill in broadcast.get_wetmills():
                for recipient in broadcast.get_recipients_for_wetmill(wetmill):
                    try:
                        text = broadcast.render(wetmill, recipient, datetime.now())

                        if text:
                            messages.append(dict(number=recipient.connection.identity, text=text, wetmill=wetmill))
                        else:
                            messages.append(dict(number=recipient.connection.identity, text=_("** No text, this wetmill would not receive a message **"), wetmill=wetmill))
                    except Exception as e:
                        messages.append(dict(number=recipient.connection.identity, text=_("** Error: %s **") % str(e), wetmill=wetmill))
                    break

            context['test_messages'] = messages
            return context

    class Schedule(SmartUpdateView):
        form_class = ScheduleForm
        title = _("Schedule Message")
        success_url = 'id@broadcasts.broadcast_read'
        submit_button_name = _("Save Broadcast")
        template_name = 'broadcasts/broadcast_schedule.html'

        def derive_initial(self, *args, **kwargs):
            initial = super(BroadcastCRUDL.Schedule, self).derive_initial(*args, **kwargs)
            if self.object.send_on:
                initial['send_date'] = self.object.send_on.date
                initial['send_time'] = self.object.send_on.strftime("%H:%M")
            else:
                initial['send_time'] = "16:00"

            return initial

        def pre_save(self, obj):
            obj = super(BroadcastCRUDL.Schedule, self).pre_save(obj)
            cleaned = self.form.cleaned_data
            if cleaned['send_date'] and cleaned['send_time']:
                obj.send_on = datetime.combine(cleaned['send_date'], cleaned['send_time'])
            else:
                obj.send_on = None
            return obj

    class Message(SmartUpdateView):
        form_class = MessageForm
        title = _("Set Message")
        success_url = 'id@broadcasts.broadcast_test'
        submit_button_name = "Schedule Broadcast"

        def get_context_data(self, *args, **kwargs):
            context = super(BroadcastCRUDL.Message, self).get_context_data(*args, **kwargs)
            
            wetmills = self.object.get_wetmills()
            context['wetmills'] = wetmills
            context['wetmill_count'] = wetmills.count()
            context['recipient_count'] = 0

            for wetmill in wetmills:
                context['recipient_count'] = context['recipient_count'] + len(self.object.get_recipients_for_wetmill(wetmill))

            for wetmill in wetmills:
                actors = self.object.get_recipients_for_wetmill(wetmill)
                if actors:
                    try:
                        preview = self.object.render(wetmill, actors[0], datetime.now())
                        sms_length = len(preview)
                        sms_count = (sms_length + 159) / 160
                        context['sms_length'] = sms_length
                        context['sms_count'] = sms_count
                        context['total_sms'] = sms_count * context['recipient_count']
                    except: # pragma: no cover
                        pass

                    break

            variables = []
            variables.append(dict(slug='wetmill.name', label="Wetmill Name"))

            if self.object.report_season:
                self.object.add_report_variables(variables)

            # add in our sms variables
            if self.object.sms_season:
                self.object.add_sms_variables(variables)
                
            context['variables'] = variables
            
            return context

    class Update(SmartUpdateView):
        form_class = BroadcastForm
        success_url = 'id@broadcasts.broadcast_read'
        title = _("Edit Recipients")

        def derive_initial(self, *args, **kwargs):
            initial = super(BroadcastCRUDL.Update, self).derive_initial(*args, **kwargs)
            if self.object.recipients.find('F') >= 0:
                initial['to_farmers'] = True
            if self.object.recipients.find('A') >= 0:
                initial['to_accountants'] = True
            if self.object.recipients.find('O') >= 0:
                initial['to_observers'] = True
            return initial

        def pre_save(self, obj):
            obj = super(BroadcastCRUDL.Update, self).pre_save(obj)
            form_data = self.form.cleaned_data

            recipients = ''
            if form_data.get('to_farmers', False):
                recipients += 'F'
            if form_data.get('to_accountants', False):
                recipients += 'A'
            if form_data.get('to_observers', False):
                recipients += 'O'

            obj.recipients = recipients

            return obj

    class Create(SmartCreateView):
        form_class = BroadcastForm
        submit_button_name = _("Set Message")
        success_url = 'id@broadcasts.broadcast_message'
        success_message = None

        def pre_save(self, obj):
            obj = super(BroadcastCRUDL.Create, self).pre_save(obj)
            form_data = self.form.cleaned_data

            recipients = ''
            if form_data.get('to_farmers', False):
                recipients += 'F'
            if form_data.get('to_accountants', False):
                recipients += 'A'
            if form_data.get('to_observers', False):
                recipients += 'O'

            obj.recipients = recipients

            return obj

    class List(SmartListView):
        fields = ('text', 'report_season', 'sms_season', 'send_on')

        def get_text(self, obj):
            if obj.text:
                return obj.text
            else:
                return "No Message Set"

    class Read(SmartReadView):
        fields = ('text', 'country', 'report_season', 'sms_season', 'send_to', 'wetmills', 'send_on', 'created_by', 'created_on')

        def derive_title(self):
            return _("SMS Broadcast")

        def get_send_to(self, obj):
            send_to = []
            for choice in obj.RECIPIENT_CHOICES:
                if obj.recipients.find(choice[0]) >= 0:
                    send_to.append(choice[1])

            return ", ".join(send_to)
        
        def get_wetmills(self, obj):
            return ", ".join([_.name for _ in obj.get_wetmills()])

