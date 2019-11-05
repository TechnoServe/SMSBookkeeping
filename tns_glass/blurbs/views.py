from smartmin.views import *
from .models import Blurb

class BlurbCRUDL(SmartCRUDL):
    model = Blurb
    actions = ('create', 'update', 'list')

    class List(SmartListView):
        fields = ('form', 'slug', 'description', 'message')
        default_order = 'form__name'

    class Update(SmartUpdateView):
        pass
