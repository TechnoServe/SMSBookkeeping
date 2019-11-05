from smartmin.views import *
from .models import *

class CSPCRUDL(SmartCRUDL):
    model = CSP
    actions = ('create', 'update', 'list')
    permissions = True

    class List(SmartListView):
        fields = ('name', 'country', 'created_by')
        add_button = True
        default_order = ('country', 'name')
