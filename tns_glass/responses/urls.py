from django.conf.urls import *
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = patterns('',
    url(r"^$", login_required(views.forms), name="xform-list"),
    url(r"^form/(\d+)/$", login_required(views.responses), name="edit-xform-responses"),
    url(r"^report/(\d+)/$", login_required(views.report_edit), name="edit-report-responses"),
)
