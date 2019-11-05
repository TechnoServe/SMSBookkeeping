from django.db import models
from django.template import Context, Template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import trans_real
from django.db.utils import DatabaseError

from rapidsms_xforms.models import XForm
from rapidsms_httprouter.router import get_router
from django.utils.translation import ugettext_lazy as _

def get_valid_reporter_types():
    """
    Returns all ContentTypes which have a 'connection' field.
    """
    ids = []

    try:
        for content_type in ContentType.objects.all():
            model = content_type.model_class()
            print "type: %s model: %s" % (content_type, model)
            
            if getattr(model, 'connection', None):
                ids.append(content_type.id)

    except DatabaseError:
        # this is probably occurring during an initial syncdb, where ContentType doesn't even
        # exist yet.  We ignore it for that reason
        pass

    return ids

class MessageCC(models.Model):
    """
    Message CC's are just that, messages that are triggered by someone else sending in a message.

    The logic to send these off is actually contained in the SMS app, but this provides a standard
    model for who is CC'ed as well as the messages actually sent.
    """
    form = models.ForeignKey(XForm, verbose_name=_("Form"))
    slug = models.SlugField(max_length=32, verbose_name=_("Slug"))
    reporter_types = models.ManyToManyField(ContentType, verbose_name=_("Reporter Types"),
                                            help_text=_("What reporter types should receive this cc, optional and up to the calling function to use."),
                                            null=True, blank=True)
#                                            limit_choices_to=dict(id__in=get_valid_reporter_types()))
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    message = models.CharField(max_length=255, verbose_name=_("Message"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))

    class Meta:
        unique_together = ('form', 'slug')

    def __unicode__(self):
        return "%s cc: %s" % (self.form.name, self.slug)

    @classmethod
    def for_form(cls, form, slug):
        """
        Returns all the CC messages that should be sent for this form.
        """
        ccs = MessageCC.objects.filter(form=form, slug=slug)
        if ccs:
            return ccs[0]
        else:
            return None

    @classmethod
    def send_cc(cls, form, slug, sender, recipients, values):
        """
        Sends CC messages to all the appropriate recipients.

          form: the form which was received
          sender: the connection of the person who sent the form
          recipients: the people who should receive the CC.  should be an iterable collection of Actors
          values: dict that will be used for any variable substitution
        """
        cc = cls.for_form(form, slug)
        if cc:
            cc.send(sender, recipients, values)

    def send(self, sender, recipients, values):
        """
        Sends CC messages to all the passed in recipient.

          sender: the connection of the person who sent the form
          recipients: the people who should receive the CC.  should be an iterable collection of Actors
          values: dict that will be used for any variable substitution
        """
        orig = trans_real.get_language()
        
        router = get_router()
        for recipient in recipients:
            try:
                # do not send to our sender
                if recipient.connection == sender:
                    continue

                # activate our language if there is one
                if getattr(recipient, 'language', None):
                    trans_real.activate(recipient.language)

                # render our message
                message = self.render_message(values)

                # and send it off
                router.add_outgoing(recipient.connection, message)
            finally:
                trans_real.activate(orig)

    def render_message(self, variables):
        """
        Renders this message, substituting any variables based on the variables passed in.
        """
        # build our template
        template = Template("{% load messages %}" + self.message)
        context = Context(variables)
        return template.render(context)
        
        

