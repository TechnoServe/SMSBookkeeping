from django.conf.urls import *

from .views import *

# set up our url patterns
urlpatterns = ExpenseCRUDL().as_urlpatterns()
