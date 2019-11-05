from smartmin.views import *
from .models import *

class FarmerPaymentCRUDL(SmartCRUDL):
    model = FarmerPayment
    permissions = True
    actions = ('create', 'update', 'list')

    class List(SmartListView):
        default_order = ('order',)
        fields = ('name', 'order', 'created_by')

    class Create(SmartCreateView):
        fields = ('name', 'order')

    class Update(SmartUpdateView):
        fields = ('is_active', 'name', 'order')


