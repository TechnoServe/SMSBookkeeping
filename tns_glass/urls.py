from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseRedirect
import locale
import rapidsms_httprouter.views as router_views

admin.autodiscover()

def set_language(request, language):
    redirect_to = request.REQUEST.get('next', '')
    active_tab = request.REQUEST.get('active_tab', '')

    # build the get paramaters to forward
    params = ''
    for param in request.REQUEST:
        if param != 'next' and param != 'active_tab':
            params += "&" + param + "=" + request.REQUEST[param]

    if active_tab:
        params += active_tab

    # this is an easy to fix to match english to LANGUAGES settings en_us
    # the settings is already used in many different places
    if language.startswith('en'):
        language = "en_us"


    request.session['django_language'] = language
    messages.success(request, "Message preference updated.")
    if redirect_to:
        if params:
            redirect_to += params
        return HttpResponseRedirect(redirect_to)
    return HttpResponseRedirect("/")

urlpatterns = patterns('',
    url(r'^users/', include('tns_users.urls')),                       
    url(r'^locales/', include('locales.urls')),
    url(r'^wetmills/', include('wetmills.urls')),
    url(r'^csps/', include('csps.urls')),
    url(r'^seasons/', include('seasons.urls')),
    url(r'^expenses/', include('expenses.urls')),
    url(r'^grades/', include('grades.urls')),
    url(r'^standards/', include('standards.urls')),
    url(r'^cashuses/', include('cashuses.urls')),
    url(r'^cashsources/', include('cashsources.urls')),
    url(r'^farmerpayments/', include('farmerpayments.urls')),
    url(r'^translate/', include('translate.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^scorecards/', include('scorecards.urls')),
    url(r'^reportimports/', include('reportimports.urls')),
    url(r'^aggregates/', include('aggregates.urls')),
    url(r'^scorecardimports/', include('scorecardimports.urls')),
    url(r'^photos/', include('photos.urls')),
    url(r'^broadcasts/', include('broadcasts.urls')),
    url(r'^broadcasts_season_end/', include('broadcasts_season_end.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^dashboardgreensales/', include('dashboard_green_sales.urls')),
    url(r'^blurbs/', include('blurbs.urls')),
    url(r'^console/', include('nsms.console.urls')),
    url(r'^help/', include('help.urls')),

    url(r'^qbs/', include('qbs.urls')),

    url(r'^', include('public.urls')),

    # django admin
    url(r'^admin/', include(admin.site.urls)),

    # setting the language
    ("^lang/(?P<language>\w+(?:-\w+)*)", set_language, {}, 'set-language'),

    # http-router
    ("^router/console", login_required(router_views.console), {}, 'httprouter-console'),

    ('', include('rapidsms_httprouter.urls')),

    # xforms
    ('', include('rapidsms_xforms.urls')),
                       
    # sms
    ('^sms/', include('sms.urls')),

    # response editor
    ('responses', include('responses.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def handler500(request):
    """
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """
    from django.template import Context, loader
    from django.http import HttpResponseServerError

    t = loader.get_template('500.html') # You need to create a 500.html template.
    return HttpResponseServerError(t.render(Context({
        'request': request,
    })))



