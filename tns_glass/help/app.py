from django.conf import settings
from datetime import datetime
import re

from rapidsms.apps.base import AppBase
from rapidsms_httprouter.router import get_router

from .models import HelpMessage

class App (AppBase):
    
    def handle (self, message):
        """
        This app is the last in the last of apps to potentially handle the message.  If we get this far
        then we should send something back that is useful to the user.
        """
        # try to find a help message for this connection
        h = HelpMessage.for_connection(message.connection)

        # if we found one, respond with that
        if h:
            message.respond(h.message)
            return True

        return False

