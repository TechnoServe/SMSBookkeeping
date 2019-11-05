from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _

CALCULATED_CHOICES = (('NONE', _("Not calculated, value is entered")),
                      ('WCAP', _("Unused Working Capital")),
                      ('CDUE', _("Cash Due from CSP")))

class CashSource(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("The name of this cash source as it will appear in the transparency sheet"))
    calculated_from = models.CharField(max_length=4, choices=CALCULATED_CHOICES, default='NONE', verbose_name=_("Calculated From"),
                                       help_text=_("How the value for this cash source is calculated, if at all"))
    order = models.IntegerField(default=0, verbose_name=_("Order"),
                                help_text=_("Controls what order this cash source will be displayed in, items with a lower order will be displayed first."))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

