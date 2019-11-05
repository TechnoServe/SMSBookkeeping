from .models import *
from smartmin.views import *

class StandardCategoryCRUDL(SmartCRUDL):
    model = StandardCategory
    actions = ('create', 'update', 'list')
    permissions = True

    class Create(SmartCreateView):
        fields = ('acronym', 'name', 'public_display', 'order')

    class Update(SmartUpdateView):
        fields = ('is_active', 'acronym', 'name', 'public_display', 'order')

    class List(SmartListView):
        fields = ('acronym', 'name', 'order')
        link_fields = ('name',)
        default_order = 'order'

class StandardCRUDL(SmartCRUDL):
    model = Standard
    actions = ('create', 'update', 'list')
    permissions = True

    class Create(SmartCreateView):
        fields = ('name', 'category', 'kind', 'order')

    class Update(SmartUpdateView):
        fields = ('is_active', 'name', 'category', 'kind', 'order')

    class List(SmartListView):
        fields = ('id', 'name', 'kind', 'category')
        link_fields = ('name',)
        default_order = ('category__order','-kind','order')
        search_fields = ('name__icontains', 'category__name__icontains')
        
        def get_kind(self, obj):
            return obj.get_kind_display()

        def get_id(self, obj):
            return "%s%d" % (obj.category.acronym, obj.order)
