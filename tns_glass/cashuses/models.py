from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _

CALCULATED_CHOICES = (('NONE', _("Not calculated, value is entered")),
                      ('PROF', _("Retained Profit")),)

class CashUse(SmartModel):
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Name"),
                            help_text=_("Name of this use of cash"))
    calculated_from = models.CharField(max_length=4, choices=CALCULATED_CHOICES, default='NONE', verbose_name=_("Calculated From"),
                                       help_text=_("How the value for this cash use is calculated, if at all"))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The order used when displayed in a list, smaller orders come first"))

    def __unicode__(self):
        return self.name
