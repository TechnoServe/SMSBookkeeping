from django import forms
import datetime
from django.utils.safestring import mark_safe
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.html import escape, conditional_escape
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

class CoordinatesPickerWidget(forms.Widget):
    """
    A widget that provides both a way of picking a point on a map
    """
    def __init__(self, attrs=None):
        # needs to be set before we are rendered
        self.country = None
        super(CoordinatesPickerWidget, self).__init__(attrs)
    
    def render(self, name, value, attrs):
        html = ''
        
        val = value['lat'] if value else ''
        html += '<input type="text" name="coordinates_lat" id="lat" value="%s" style="width:150px;margin-right:10px;text-align:right">' % val

        val = value['lng'] if value else ''
        html += '<input type="text" name="coordinates_lng" id="lng" value="%s" style="width:150px;text-align:right">' % val

        # also include the center and zoom level for this country
        html += '<input type="hidden" id="map_lat" value="%s">' % self.country.bounds_lat
        html += '<input type="hidden" id="map_lng" value="%s">' % self.country.bounds_lng
        html += '<input type="hidden" id="map_zoom" value="%s">' % self.country.bounds_zoom    

        return mark_safe(force_unicode(html))

    def value_from_datadict(self, data, files, name):
        lat = data.get('coordinates_lat')
        lng = data.get('coordinates_lng')

        if lat and lng:
            return dict(lat=lat, lng=lng)
        else:
            return None

    class Media:
       js = ('http://maps.google.com/maps/api/js?sensor=false', 'js/coordinates_picker.js')
    
class CoordinatesPickerField(forms.Field):
    widget = CoordinatesPickerWidget

    def set_country(self, country):
        self.widget.country = country

    def validate(self, value):
        if value:
            error = False
            if 'lat' in value:
                if value['lat'].find(',') != -1:
                    error = True

            if 'lng' in value:
                if value['lng'].find(',') != -1:
                    error = True

            if error:
                raise ValidationError(_('The latitude and longitude coordinates should use "." instead of ","'))

        return value

class BoundsWidget(forms.Widget):
    """
    A widget that provides an interactive map for the user to pick from
    """
    def __init__(self, attrs=None):
        super(BoundsWidget, self).__init__(attrs)

    def render(self, name, value, attrs):
        val = "Zoom: %s Center: %s, %s" % (value.get('zoom', ''), value.get('lat', ''), value.get('lng', '')) if value else ''
        html = '<span id="bounds_value">%s</span>' % val

        val = value.get('lat', '') if value else ''
        html += '<input type="hidden" name="%s_lat" id="bounds_lat" value="%s">' % (name, val)

        val = value.get('lng', '') if value else ''
        html += '<input type="hidden" name="%s_lng" id="bounds_lng" value="%s">' % (name, val)

        val = value.get('zoom', '') if value else ''
        html += '<input type="hidden" name="%s_zoom" id="bounds_zoom" value="%s">' % (name, val)

        safe = mark_safe(force_unicode(html))
        return safe

    def value_from_datadict(self, data, files, name):
        lat = data.get('bounds_lat')
        lng = data.get('bounds_lng')
        zoom = data.get('bounds_zoom')

        if lat and lng and zoom:
            return dict(lat=lat, lng=lng, zoom=zoom)
        else:
            return None

    class Media:
       js = ('http://maps.google.com/maps/api/js?sensor=false', 'js/bounds_picker.js')
        
class BoundsField(forms.Field):
    widget = BoundsWidget
