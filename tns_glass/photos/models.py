from django.db import models
from sorl.thumbnail import ImageField
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _
from wetmills.models import Wetmill

class Photo(SmartModel):
    caption = models.CharField(max_length=64, blank=True, verbose_name=_("Caption"),
                               help_text=_("A brief description for this photo (optional)"))
    image_width = models.PositiveIntegerField(verbose_name=_("Image Width"))
    image_height = models.PositiveIntegerField(verbose_name=_("Image Height"))
    image = models.ImageField(upload_to='photos/', height_field='image_height', width_field='image_width', verbose_name=_("Image"),
                              help_text=_("Choose an image from your computer, jpg"))
    wetmill = models.ForeignKey(Wetmill, related_name='photos', verbose_name=_("Wetmill"),
                                help_text=_("Choose the wetmill for this photo"))
    is_main = models.BooleanField(default=False, verbose_name=_("Is Main"),
                                  help_text=_("Make this photo the main photo on the wetmill page"))

    def get_resolution(self):
        if self.image_height < 600 and self.image_width < 800:
            return '%sx%s' % (self.image_width, self.image_height)
        else:
            return '800x600'
