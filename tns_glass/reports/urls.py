from .views import *

urlpatterns = ReportCRUDL().as_urlpatterns()
urlpatterns += SaleCRUDL().as_urlpatterns()
