from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _

class StandardCategory(SmartModel):
    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"),
                            help_text=_("Name this category"))
    acronym = models.SlugField(max_length=64, unique=True, verbose_name=_("Acronym"),
                               help_text=_("The acronym of this category"))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The order this category will displayed in list, smaller orders come first"))
    public_display = models.BooleanField(default=True, verbose_name=_("Pulic Display"),
                                        help_text=_("Whether to display the score for this category on the public wetmill page for finalized scorecards"))

    class Meta:
        verbose_name_plural = _("Standard Categories")

    def __unicode__(self):
        return self.name

class Standard(SmartModel):
    name = models.CharField(max_length=64, verbose_name=_("Name"),
                            help_text=_("Name this standard"))
    category = models.ForeignKey(StandardCategory, verbose_name=_("Category"),
                                 help_text=_("The category this standard belongs to"))
    kind = models.CharField(max_length=2,choices=(('MR',_('Minimum Requirement')),('BP', _('Best Practice'))),
                               help_text=_("What kind of standard is this"))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The order used when displayed in lists, standards with smaller orders come first"))

    def acronym(self):
        return "%s%d" % (self.category.acronym, self.order)

    def __unicode__(self):
        return "%s%d - %s" % (self.category.acronym, self.order, self.name)

    class Meta:
        unique_together = ('category', 'name')
