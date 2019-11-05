from smartmin.views import *
from .models import *

class CashSourceCRUDL(SmartCRUDL):
    permissions = True
    model = CashSource
    actions = ('create', 'update', 'list')

    class List(SmartListView):
        default_order = ('order',)
        fields = ('name', 'order', 'created_by')

    class Create(SmartCreateView):
        fields = ('name', 'calculated_from', 'order')

    class Update(SmartUpdateView):
        fields = ('is_active', 'name', 'calculated_from', 'order')

