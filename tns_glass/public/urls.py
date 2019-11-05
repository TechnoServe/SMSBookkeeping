from django.conf.urls import patterns, include, url
from .views import home, country_home, wetmill_home, search

urlpatterns = patterns('',
    url(r'^$', home, name='public-home'),
    url(r'^c/(.*)/$', country_home, name='public-country'),
    url(r'^w/search/$', search, name='public-search'),
    url(r'^w/(.*)/$', wetmill_home, name='public-wetmill'),
)
