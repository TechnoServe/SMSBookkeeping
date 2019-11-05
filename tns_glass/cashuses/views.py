from smartmin.views import *
from .models import *

class CashUseCRUDL(SmartCRUDL):
    model = CashUse
    actions = ('create', 'update', 'list')
    permissions = True

    class List(SmartListView):
        fields = ('name', 'order')
        default_order = ('order',)

    class Create(SmartCreateView):
        fields = ('name', 'calculated_from', 'order')

    class Update(SmartUpdateView):
        fields = ('is_active', 'name', 'calculated_from', 'order')
