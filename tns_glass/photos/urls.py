from .views import *

# set up our url patterns
urlpatterns = PhotoCRUDL().as_urlpatterns()
