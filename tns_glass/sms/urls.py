from django.conf.urls import *
from . import views

urlpatterns = patterns('',
    url(r'^router/(\w+)/$', views.submission_actor, name='submission_actor'),
    url(r'^router/(\w+)/(\d+)/$', views.submission_actor, name='submission_actor'),

    url(r'^wetmill/(\d+)/$', views.sms_view, name='sms-view'),
    url(r'^wetmill/(\d+)/(\d+)/$', views.sms_view, name='sms-view'),
    url(r'^wetmill/(\d+)/disassociate/(\d+)/$', views.sms_disassociate, name='sms-disassociate'),

    url(r'^wetmill/(\d+)/(\d+)/clear/$', views.sms_clear, name='sms-clear'),
)

urlpatterns += views.AmafarangaCRUDL().as_urlpatterns()
urlpatterns += views.SitokiCRUDL().as_urlpatterns()
urlpatterns += views.IbitumbweCRUDL().as_urlpatterns()
urlpatterns += views.TwakinzeCRUDL().as_urlpatterns()
urlpatterns += views.IgurishaCRUDL().as_urlpatterns()
urlpatterns += views.DepanseCRUDL().as_urlpatterns()