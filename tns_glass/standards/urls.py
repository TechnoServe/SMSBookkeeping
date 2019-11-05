from django.conf.urls import *

from .views import *

# set up our url patterns
urlpatterns = StandardCategoryCRUDL().as_urlpatterns()
urlpatterns += StandardCRUDL().as_urlpatterns()
