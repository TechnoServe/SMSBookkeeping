"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from rapidsms_xforms.models import XForm, XFormField
from rapidsms.messages.incoming import IncomingMessage
from .models import *
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import pytz
from rapidsms.models import Backend, Connection

class HelpTest(TestCase):

    def test_help(self):
        backend, created = Backend.objects.get_or_create(name='tester')
        connection, created = Connection.objects.get_or_create(backend=backend, identity='5551212')
        
        self.assertEquals(None, HelpMessage.for_connection(connection))

        # add a help message
        reporter_type = ContentType.objects.get_for_model(HelpReporter)        
        help_known = HelpMessage.objects.create(reporter_type=reporter_type,
                                                message="Try sending 'forex'",
                                                priority=1)


        # test that we still get nothing
        self.assertEquals(None, HelpMessage.for_connection(connection))

        # now add a default rule
        help_default = HelpMessage.objects.create(message="You are nobody")
        self.assertEquals(help_default, HelpMessage.for_connection(connection))

        # finally, create a real reporter and make sure that matches
        HelpReporter.objects.create(connection=connection)

        self.assertEquals(help_known, HelpMessage.for_connection(connection))        


