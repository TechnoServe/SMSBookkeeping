from smartmin.views import *
from .models import BroadcastsOnSeasonEnd

from wetmills.models import Wetmill
from seasons.models import Season

from datetime import datetime


class BroadcastsOnSeasonEndCRUDL(SmartCRUDL):
    actions = ('create', 'list', 'read', 'preview')
    model = BroadcastsOnSeasonEnd
    permissions = False

    class Create(SmartCreateView):
        fields = ('name', 'recipients', 'text', 'description')

    class List(SmartListView):
        fields = ('name', 'send_to', 'text')

        def get_send_to(self, obj):
            send_to = []
            for choice in obj.RECIPIENT_CHOICES:
                if obj.recipients.find(choice[0]) >= 0:
                    send_to.append(choice[1])

            return ", ".join(send_to)

    class Read(SmartReadView):
        fields = ('name', 'send_to', 'text', 'description', 'created_on', 'created_by')

        def get_send_to(self, obj):
            send_to = []
            for choice in obj.RECIPIENT_CHOICES:
                if obj.recipients.find(choice[0]) >= 0:
                    send_to.append(choice[1])

            return ", ".join(send_to)

    class Preview(SmartReadView):
        fields = ('name', 'recipients', 'text')
        template_name = 'broadcasts_season_end/send.html'

        def derive_title(self):
            return "Send Farmer Transparency Messages"

        def get_recipients(self, obj):
            return obj.get_recipients_display()

        def get_context_data(self, *args, **kwargs):
            context = super(BroadcastsOnSeasonEndCRUDL.Preview, self).get_context_data(*args, **kwargs)
            messages = []

            broadcast_template = self.object

            wetmill_id = self.request.REQUEST.get('wetmill', None)
            wetmill = None
            if wetmill_id:
                wetmill = Wetmill.objects.get(pk=wetmill_id)

            season_id = self.request.REQUEST.get('season', None)
            season = None
            if season_id:
                season = Season.objects.get(pk=season_id)

            for recipient in broadcast_template.get_recipients_for_wetmill(wetmill):
                try:
                    text = broadcast_template.render(wetmill, season, recipient, datetime.now())

                    if text:
                        messages.append(dict(number=recipient.connection.identity, text=text, wetmill=wetmill))
                    else:
                        messages.append(dict(number=recipient.connection.identity, text=_("** No text, this wetmill would not receive a message **"), wetmill=wetmill))
                except Exception as e:
                    messages.append(dict(number=recipient.connection.identity, text=_("** Error: %s **") % str(e), wetmill=wetmill))
                break

            context['test_messages'] = messages
            return context