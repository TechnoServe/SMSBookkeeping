from django.db import models
from django.db.utils import DatabaseError

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

def get_valid_reporter_types():
    """
    Returns all ContentTypes which have a 'connection' field.
    """
    ids = []

    try:
        for content_type in ContentType.objects.all():
            model = content_type.model_class()
            if getattr(model, 'connection', None):
                ids.append(content_type.id)

    except DatabaseError:
        # this is probably occurring during an initial syncdb, where ContentType doesn't even
        # exist yet.  We ignore it for that reason
        pass

    return ids

class HelpMessage(models.Model):
    """
    Help Messages are sent when an unrecognized message comes in.

    We can optionally set what message to send based on the reporter type of the person sending
    the message.  This can be done by specifying more than one help message, one for each
    type of reporter.
    """
    message = models.CharField(max_length=160, verbose_name=_("Message"), help_text=_("The message to send back to the user."))
    reporter_type = models.ForeignKey(ContentType, blank=True, null=True, unique=True, verbose_name=_("Reporter Type"),
                                      help_text=_("Our reporter object type, must contain a 'connection' field."))
#                                      limit_choices_to=dict(id__in=get_valid_reporter_types()))
    priority = models.IntegerField(default=0, verbose_name=_("Priority"),
                                   help_text=_("The priority of our help message, matches will be attempted from highest to lowest"))


    def __unicode__(self):
        return "%s (%s - %d)" % (self.message, self.reporter_type, self.priority)


    @classmethod
    def for_connection(cls, connection):
        """
        Returns the appropriate help message for the passed in connection.
        """
        for h in HelpMessage.objects.all().order_by("-priority"):
            # no reporter type means this is a catch all
            if not h.reporter_type:
                return h

            # otherwise, see if we can find a reporter with this connection
            model = h.reporter_type.model_class()
            matches = model.objects.filter(connection=connection)
            if matches:
                return h

        # no matching rules found, oh well
        return None

                
import sys
if sys.argv[1] == 'test':
    # This is a bit hacky, see
    # http://code.djangoproject.com/ticket/7835

    from rapidsms.models import Connection

    # this is only here to define a concrete model that we can test with
    class HelpReporter(models.Model):
        connection = models.ForeignKey(Connection)

