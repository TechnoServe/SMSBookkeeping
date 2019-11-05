from django.conf.urls import *

from .views import *

# set up our url patterns
urlpatterns = CountryCRUDL().as_urlpatterns()
urlpatterns += CurrencyCRUDL().as_urlpatterns()
urlpatterns += ProvinceCRUDL().as_urlpatterns()
urlpatterns += WeightCRUDL().as_urlpatterns()
