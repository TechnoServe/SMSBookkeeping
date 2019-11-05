# Django settings for tns_glass project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

HOSTNAME = 'www.your-website.com'
ALLOWED_HOSTS = ['.your-website.com', '.your-otherwebsite.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'tnsglass.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone
TIME_ZONE = 'GMT'
USER_TIME_ZONE = 'Africa/Kigali'

MODELTRANSLATION_TRANSLATION_REGISTRY = "translation"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Available languages for translation
LANGUAGES = (('en_us', "English"), 
             ('rw', "Kinyarwanda"), 
             ('ke_sw', "Kenyan Swahili" ), 
             ('tz_sw', "Tanzanian Swahili"),
             ('es', "Spanish"),
             ('am', "Amharic"))

# models that we don't want included in our master translate app
EXCLUDED_TRANSLATE_MODELS = ('rapidsms_xforms.models.XForm', 
                             'rapidsms_xforms.models.XFormField', 
                             'rapidsms_xforms.models.XFormFieldConstraint')

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n7#^+-u-#1wm=y3a$-#^jps5tihx5v_@-_(kxumq_$+$5r)bxo'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',    
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'tns_glass.urls'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django-cache'
    }
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.markup',
    'django.contrib.humanize',

    'south',

    # mo-betta permission management
    'guardian',

    # thumbnailing
    'sorl.thumbnail',

    # the django admin
    'django.contrib.admin',

    # debug!
    'debug_toolbar',

    # compress our CSS and js
    'compressor',

    'util',

    'smartmin',
    'rosetta',
    'modeltranslation',

    'django_quickblocks',
    'django_select2',

    # async tasks,
    'djcelery',

    'smartmin.users',
    'tns_users',
    'perms',
    'translate',
    'locales',
    'wetmills',
    'csps',
    'seasons',
    'expenses',
    'grades',
    'standards',
    'cashuses',
    'cashsources',
    'farmerpayments',
    'public',
    'canvas',
    'reports',
    'scorecards',
    'reportimports',
    'aggregates',
    'scorecardimports',
    'photos',
    'reminders',
    'nsms.console',

    # sms apps
    'rapidsms',
    'rapidsms_httprouter',
    'eav',
    'uni_form',
    'django_digest',
    'rapidsms_xforms',
    'responses',
    'sms',
    'help',
    'cc',
    'blurbs',
    'sms_reports',
    'broadcasts',
    'broadcasts_season_end',
    'dashboard',
    'dashboard_green_sales',
    'dashboard_green_sales_charts',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
     'require_debug_false': {
         '()': 'django.utils.log.RequireDebugFalse'
     }
    },
    'handlers': {
        'mail_admins': {
            'filters': [ 'require_debug_false' ],
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

#-----------------------------------------------------------------------------------
# Directory Configuration
#-----------------------------------------------------------------------------------
import os

PROJECT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))
RESOURCES_DIR = os.path.join(PROJECT_DIR, '../resources')

LOCALE_PATHS = (os.path.join(PROJECT_DIR, './locale'),)

RESOURCES_DIR = os.path.join(PROJECT_DIR, '../resources')
FIXTURE_DIRS = (os.path.join(PROJECT_DIR, '../fixtures'),)
TESTFILES_DIR = os.path.join(PROJECT_DIR, '../testfiles')
TEMPLATE_DIRS = (os.path.join(PROJECT_DIR, '../templates'),)
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, '../static'), os.path.join(PROJECT_DIR, '../media'), )
STATIC_ROOT = os.path.join(PROJECT_DIR, '../sitestatic')
MEDIA_ROOT = os.path.join(PROJECT_DIR, '../media')
MEDIA_URL = "/media/"

#-----------------------------------------------------------------------------------
# Permission Management
#-----------------------------------------------------------------------------------

# this lets us easily create new permissions across our objects
PERMISSIONS = {
    '*': ('create', # can create an object
          'read',   # can read an object, viewing it's details
          'update', # can update an object
          'delete', # can delete an object,
          'list'),  # can view a list of the objects
    'wetmills.wetmill': ('country', 'wetmill_edit', 'report_view', 'scorecard_view', 'report_edit', 'scorecard_edit', 'csps', 'sms_view', 'sms_edit', 'accounting'),
    'locales.country': ('pick', 'wetmill_edit', 'report_view', 'scorecard_view', 'report_edit', 'scorecard_edit', 'translate', 'sms_view', 'sms_edit'),
    'csps.csp': ('wetmill_edit', 'report_view', 'scorecard_view', 'report_edit', 'scorecard_edit', 'sms_view', 'sms_edit'),
    'auth.user': ('permissions', 'profile'),
    'reports.report': ('lookup', 'attributes', 'production', 'expenses', 'pdf', 'finalize', 'credit_only'),
    'scorecards.scorecard': ('lookup', 'standards', 'pdf', 'finalize'),
    'reportimports.reportimport': ('action', 'import'),
    'scorecardimports.scorecardimport': ('action', 'import'),
    'wetmills.wetmillimport': ('import',),
    'aggregates.finalizetask': ('finalize',),
    'seasons.season': ('clone',),
    'broadcasts.broadcast': ('preview', 'message', 'schedule', 'test'),
    'dashboard.assumptions': ('output', 'change', 'dashboard'),
    'broadcastsbroadcasts_season_end.broadcastsonseasonend': ('create', 'read', 'update', 'preview')
}

# assigns the permissions that each group should have
GROUP_PERMISSIONS = {
    "Administrators": (
        'locales.currency.*','locales.weight.*', 'locales.country.*', 'locales.province.*', 'csps.csp.*',
        'seasons.season.*', 'grades.grade.*', 'wetmills.wetmill.*', 'wetmills.wetmillimport.*', 'auth.user.*',
        'expenses.expense.*', 
        'standards.standardcategory.*','standards.standard.*',
        'reports.report.*', 'reports.sale.*',
        'cashuses.cashuse.*',
        'cashsources.cashsource.*',
        'farmerpayments.farmerpayment.*',
        'scorecards.scorecard.*', 'scorecardimports.scorecardimport.*',
        'reportimports.reportimport.*',
        'aggregates.finalizetask.*',
        'photos.photo.*',
        'django_quickblocks.quickblock.*', 'django_quickblocks.quickblocktype.*',
        'help.helpmessage.*',
        'broadcasts.broadcast.*',
        'dashboard.assumptions.*',
        'rapidsms_httprouter.message.*',
        'broadcasts_season_end.broadcastsonseasonend.*', 'broadcasts_season_end.broadcastsonseasonend_preview'
    ),
    "Country Administrators": (
        'locales.province.*', 'csps.csp.*',
        'seasons.season.*', 'wetmills.wetmill.*', 'wetmills.wetmillimport.*',
        'reports.report.*', 'reports.sale.*',
        'scorecards.scorecard.*', 'scorecardimports.scorecardimport.*',
        'reportimports.reportimport.*',
        'aggregates.finalizetask.*',
        'locales.country_translate',
        'help.helpmessage.*',
        'broadcasts.broadcast.*',
        'dashboard.assumptions.*',
        'auth.user_profile',
        'broadcasts_season_end.broadcastsonseasonend.*', 'broadcasts_season_end.broadcastsonseasonend_preview',
    ),
    "SMS Administrators": (
        'help.helpmessage.*', 'broadcasts.broadcast.*', 'dashboard.assumptions.*', 'auth.user_profile',
        'rapidsms_httprouter.message.*',
    ),
    "CSP Administrators": (
        'auth.user_profile',
    ),
    "CSP Users": (
        'auth.user_profile',
    ),
    "Viewer": (
        'auth.user_profile',
    ),
    "Compliance Officers": (),
    "Web Accountant": (
        'auth.user_profile',
    ),
    "Private Wet Mill Owners": (
        'help.helpmessage.*', 'auth.user_profile',
    ),
    "Financial Institution Member": (
        'help.helpmessage.*', 'auth.user_profile', 'reports.report_credit_only',
        'reports.report.*',
    )
}


#-----------------------------------------------------------------------------------
# Login / Logout
#-----------------------------------------------------------------------------------
LOGIN_URL = "/users/login/"
LOGOUT_URL = "/users/logout/"
LOGIN_REDIRECT_URL = "/"

#-----------------------------------------------------------------------------------
# Guardian Configuration
#-----------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ANONYMOUS_USER_ID = -1

#-----------------------------------------------------------------------------------
# Async tasks with django-celery
#-----------------------------------------------------------------------------------

import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = 'redis'
BROKER_HOST = 'localhost'
BROKER_PORT = 6379
BROKER_VHOST = '2'

CELERY_CONCURRENCY = 4
CELERYD_PREFETCH_MULTIPLIER = 16

REDIS_PORT = 6379
REDIS_HOST = 'localhost'
REDIS_DB = 2

#-----------------------------------------------------------------------------------
# Crontab Schedule
#-----------------------------------------------------------------------------------

from datetime import timedelta
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "resend-errors": {
        'task': 'rapidsms_httprouter.tasks.resend_errored_messages_task',
        'schedule': timedelta(minutes=5),
    },

    "send-broadcasts": {
        'task': 'broadcasts.tasks.send_broadcasts',
        'schedule': timedelta(minutes=5),
    },

    "daily-reminders": {
        'task': 'reminders.tasks.check_daily_reminders',
        'schedule': crontab(minute='0',
                            hour='14')
    },

    "weekly-reminders": {
        'task': 'reminders.tasks.check_weekly_reminders',
        'schedule': crontab(minute='0',
                            hour='14',
                            day_of_week='mon')
    },

    "save_nyc_price": {
        'task': 'dashboard.tasks.save_nyc_price',
        'schedule': crontab(minute=0,
                            hour=[14, 15, 16, 17, 18, 19, 20, 21, 22])
    },

    "update_exchange_rate": {
        'task': 'dashboard.tasks.update_exchange_rate',
        'schedule': crontab(minute=0,
                            hour=14),
    },
}

#-----------------------------------------------------------------------------------
# Django-Nose config
#-----------------------------------------------------------------------------------

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

SOUTH_TESTS_MIGRATE = False

#-----------------------------------------------------------------------------------
# SMS Configs
#-----------------------------------------------------------------------------------

RAPIDSMS_TABS = []
SMS_APPS = ['sms', 'rapidsms_xforms', 'help']

#-----------------------------------------------------------------------------------
# Debug Toolbar
#-----------------------------------------------------------------------------------

INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_CONFIG = {
   'INTERCEPT_REDIRECTS': False,
}

#-----------------------------------------------------------------------------------
# Coffee price lookup
#-----------------------------------------------------------------------------------
NYC_PRICE_URL = 'http://www.barchart.com/quotes/futures/KCK{{YEAR}}'
NYC_PRICE_SELECTOR = '#dtaLast'

#-----------------------------------------------------------------------------------
# Maps backend names to the country code so we can properly route messages
#-----------------------------------------------------------------------------------
BACKEND_TO_COUNTRY_MAP = {
  'tns': 'RW',
  'tz': 'TZ',
  'tz_tester': 'TZ',
  'et': 'ET',
  'et_tester': 'ET',
  'tns_tester': 'RW',
  'ss': 'SS',
}

#-----------------------------------------------------------------------------------
#  Exchange Rate Lookup
#-----------------------------------------------------------------------------------
#Google
EXCHANGE_RATE_INFO_URL = 'https://www.google.com/finance/converter?a=1&from=USD&to={{CURRENCY_CODE}}'
CURRENCY_PRICE_SELECTOR = '.bld'
