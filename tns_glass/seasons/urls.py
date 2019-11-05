from django.conf.urls import *

from .views import *

# set up our url patterns
urlpatterns = SeasonCRUDL().as_urlpatterns()
