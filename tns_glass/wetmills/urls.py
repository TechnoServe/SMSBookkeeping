from .views import *

urlpatterns = WetmillCRUDL().as_urlpatterns()
urlpatterns += WetmillImportCRUDL().as_urlpatterns()
