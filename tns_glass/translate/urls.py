from django.conf.urls import patterns, include, url
from .views import index, db

urlpatterns = patterns('',
    url(r'^db/(\w+)/', db, name='translate_db'),
    url(r'^pofile/$', 'rosetta.views.home', name='rosetta-home'),
    url(r'^$', index, name='translate_index'),
    url(r'^download/$', 'rosetta.views.download_file', name='rosetta-download-file'),
    url(r'^select/(?P<langid>[\w\-]+)/(?P<idx>\d+)/$','rosetta.views.lang_sel', name='rosetta-language-selection'),
)

