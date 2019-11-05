from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _

class FarmerPayment(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("The name of for this farmer payment as it will appear in the transparency sheet"))
    order = models.IntegerField(default=0, verbose_name=_("Order"),
                                help_text=_("Controls what order this farmer payment will be displayed in, items with a lower order will be displayed first."))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

        


