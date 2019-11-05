from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _
# Create your models here.
class CSP(SmartModel):
    country = models.ForeignKey('locales.Country', verbose_name=_("Country"),
                                help_text=_("What country does this CSP operate in"))
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("The name of this CSP in English"))
    sms_name = models.SlugField(max_length=16, unique=True, verbose_name=_("SMS Name"),
                                help_text=_("A short, simple name that will be used to refer to this CSP in SMS messages"))
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name=_("Logo"),
                             help_text=_("A logo for the CSP, optional"))
    description = models.TextField(verbose_name=_("Description"), help_text=_("A brief description for this CSP, history, background etc.."))

    def __unicode__(self):
        return "%s" % (self.name,)

    class Meta:
        verbose_name = _('Coffee Service Provider')
        verbose_name_plural = _('Coffee Service Providers')
        ordering = ('country__name', 'name', )

