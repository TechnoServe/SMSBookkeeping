from django.db import models
from django.template import Context, Template
from rapidsms_xforms.models import XForm
from django.utils.translation import ugettext_lazy as _

class Blurb(models.Model):
    """
    A blurb simply represents some text that is tied to an XForm.  It is a way of
    having messages tied to forms and in the database to allow for translation.
    """
    form = models.ForeignKey(XForm, verbose_name=_("Form"))
    slug = models.SlugField(verbose_name=_("Slug"))
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    message = models.CharField(max_length=255, verbose_name=_("Message"))

    class Meta:
        unique_together = ('form', 'slug')

    @classmethod
    def get(cls, form, slug, variables, default):
        """
        Looks up the blurb for the passed in form and slug and renders it with the passed in variables.

        If no blurb is found, then the default values are used.
        """
        blurb = Blurb.objects.filter(form=form, slug=slug)
        if blurb:
            template = blurb[0].message
        else:
            # create an empty blurb object, we want it there so they can fill it out
            Blurb.objects.create(form=form, slug=slug, description=default, message=default)
            template = default

        return render(template, variables)

    def __unicode__(self):
        return "%s (%s)" % (self.form.name, self.slug)


def render(message, variables):
    """
    Renders a template given a template string and values to substitute.
    """
    try:
        template = Template("{% load messages %}" + message)
        context = Context(variables)
        return template.render(context)
    except:
        return message
