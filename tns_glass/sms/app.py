from django.conf import settings
from datetime import datetime

from rapidsms.apps.base import AppBase
from rapidsms_httprouter.router import get_router

from .models import *

from django.utils.translation import activate

class App (AppBase): # pragma: no cover

    # we snoop on messages to set the language
    def parse(self, message):
        # do we recognize this connection as an accountant?
        accs = Accountant.objects.filter(connection=message.connection).order_by('-created')
        if accs:
            language = accs[0].language

            # activate that language
            activate(language)

        else:
            country = get_country_for_backend(message.connection.backend.name)
            activate(country.language)

    # always bring our language back to english after sms processing
    def cleanup(self, message):
        activate('en-us')

    # always bring our language back to english after sms processing
    def outgoing(self, message):
        activate('en-us')
    


