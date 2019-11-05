from .views import *

urlpatterns = AssumptionsCRUDL().as_urlpatterns()
urlpatterns += DashboardCRUDL().as_urlpatterns()
