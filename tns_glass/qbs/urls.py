from django_quickblocks.views import QuickBlockTypeCRUDL, QuickBlockImageCRUDL
from .views import LocalizedQuickBlockCRUDL

urlpatterns = LocalizedQuickBlockCRUDL().as_urlpatterns()
urlpatterns += QuickBlockTypeCRUDL().as_urlpatterns()
urlpatterns += QuickBlockImageCRUDL().as_urlpatterns()