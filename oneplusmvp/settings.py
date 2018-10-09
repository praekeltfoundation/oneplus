"""
Django settings for oneplusmvp project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import djcelery
import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

djcelery.setup_loader()


def abspath(*args):
    """convert relative paths to absolute paths relative to PROJECT_ROOT"""
    return os.path.join(PROJECT_ROOT, *args)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '2*pv1ow5a6l^+h&ea#jy63#k4hw&lo2b_wy+9d+^_c#sce0at5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

BASE_URL = 'oneplus.qa.praekeltfoundation.org'
# os.path.join(BASE_DIR, "oneplus/templates")

ALLOWED_HOSTS = ['*']

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'oneplus.context_processors.social_media',
)
# Application definition

SITE_ID = 1

INSTALLED_APPS = (
    "mobileu",
    "oneplus",
    "grappelli",
    "import_export",
    "communication",
    "auth",
    "core",
    "gamification",
    "content",
    "djcelery",
    "organisation",
    "django_summernote",
    "south",
    "django_bleach",
    "bs4",
    "google_analytics",
    "pwa",
    "raven.contrib.django.raven_compat",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "django.contrib.auth",
    "daterange_filter"
)

MIDDLEWARE_CLASSES = (
    'lockout.middleware.LockoutMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

LOCKOUT_MAX_ATTEMPTS = 15
LOCKOUT_TIME = 900
LOCKOUT_ENFORCEMENT_WINDOW = 600

ROOT_URLCONF = 'oneplusmvp.urls'

WSGI_APPLICATION = 'oneplusmvp.wsgi.application'

# Close the session when user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

AUTH_USER_MODEL = "auth.CustomUser"

TEST_RUNNER = 'core.tests.TestRunner'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'oneplus',
        'USER': 'oneplus',
        'PASSWORD': 'oneplus',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://127.0.0.1:9200/')
ELASTICSEARCH_INDEX_PREFIX = os.environ.get('ELASTICSEARCH_INDEX_PREFIX', 'oneplus_')

GOOGLE_ANALYTICS = {
    'google_analytics_id': 'UA-52417331-1',
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Johannesburg'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
ENV_PATH = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(ENV_PATH, 'media/')
MEDIA_URL = "/media/"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = abspath('static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

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
)

# Junebug config
JUNEBUG_BASE_URL = os.environ.get("JUNEBUG_BASE_URL", "")
JUNEBUG_CHANNEL_ID = os.environ.get("JUNEBUG_CHANNEL_ID", "")
JUNEBUG_ACCOUNT_NUMBER = os.environ.get("JUNEBUG_ACCOUNT_NUMBER", "")
JUNEBUG_FAKE = os.environ.get("JUNEBUG_FAKE", "")
JUNEBUG_FAKE_TO = os.environ.get("JUNEBUG_FAKE_TO", "")
JUNEBUG_USERNAME = os.environ.get("JUNEBUG_USERNAME", "")
JUNEBUG_PASSWORD = os.environ.get("JUNEBUG_PASSWORD", "")
JUNEBUG_AUTHORISATION_TYPE = os.environ.get("JUNEBUG_AUTHORISATION_TYPE", "")

IMPORT_EXPORT_USE_TRANSACTIONS = True

# Which HTML tags are allowed
BLEACH_ALLOWED_TAGS = ['img', 'p', 'b', 'i', 'u', 'em', 'strong', 'a']

# Which HTML attributes are allowed
BLEACH_ALLOWED_ATTRIBUTES = ['href', 'title', 'style', 'src']

# Which CSS properties are allowed in 'style' attributes (assuming
# style is an allowed attribute)
BLEACH_ALLOWED_STYLES = [
    'font-family', 'font-weight', 'text-decoration', 'font-variant',
    'width', 'height']

# Strip unknown tags if True, replace with HTML escaped characters if
# False
BLEACH_STRIP_TAGS = True

# Strip comments, or leave them in.
BLEACH_STRIP_COMMENTS = False

# The number of correct answers in a week required to win airtime
ONEPLUS_WIN_REQUIRED = 12

# Airtime to win per week in Rands
ONEPLUS_WIN_AIRTIME = 5

GRAPPELLI_ADMIN_TITLE = "dig-it Admin"

SUMMERNOTE_CONFIG = {
    # Change editor size
    'width': '100%',
    'height': '400',

    # Customize toolbar buttons
    'toolbar': [
        ['style', ['style']],
        ['style', ['bold', 'italic', 'underline', 'clear']],
        ['para', ['ul', 'ol', 'paragraph']],
        ['insert', ['link', 'picture']],
        ['table', ['table']],
    ],
    'default_css': (
        '//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css',
        os.path.abspath('django_summernote/summernote.css'),
        os.path.abspath('django_summernote/django_summernote.css'),
    ),
    'default_js': (
        '//code.jquery.com/jquery-1.9.1.min.js',
        '//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js',
        os.path.abspath('django_summernote/jquery.ui.widget.js'),
        os.path.abspath('django_summernote/jquery.iframe-transport.js'),
        os.path.abspath('django_summernote/jquery.fileupload.js'),
        os.path.abspath('django_summernote/summernote.min.js'),
    ),
    'css': (),
    'js': (),

    'default_css_for_inplace': (
        '//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css',
        os.path.abspath('django_summernote/summernote.css'),
        os.path.abspath('django_summernote/django_summernote_inplace.css'),
    ),
    'default_js_for_inplace': (
        '//code.jquery.com/jquery-1.9.1.min.js',
        '//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js',
        os.path.abspath('django_summernote/jquery.ui.widget.js'),
        os.path.abspath('django_summernote/jquery.iframe-transport.js'),
        os.path.abspath('django_summernote/jquery.fileupload.js'),
        os.path.abspath('django_summernote/summernote.min.js'),
    ),
    'css_for_inplace': (),
    'js_for_inplace': (),
    # Disable upload
    'disable_upload': False,
}

CELERY_IMPORTS = ('mobileu.tasks', 'communication.tasks')
CELERY_RESULT_BACKEND = "database"
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
# The minimum number of SMSes that can be sent before being sent with celery
MIN_JUNEBUG_CELERY_SEND = 1

FIXTURE_DIRS = (
    abspath('fixtures'),
    abspath('../oneplus/fixtures')
)

USE_TZ = False

EMAIL_HOST = 'localhost'
EMAIL_PORT = '25'
SERVER_EMAIL = 'info@dig-it.me'
EMAIL_SUBJECT_PREFIX = '[DIG-IT] '
MANAGERS = (
    ('Jane', 'info@dig-it.me'),
)

MATHML_URL = 'http://mathml.p16n.org/'

ADMIN_REORDER = (
    ("Auth", ("Course Managers", "Course Mentors", "Groups", "Learners", "Teachers", "School Managers",
              "System Administrators")),
)

GRADE_10_COURSE_NAME = "One Plus Grade 10"
GRADE_11_COURSE_NAME = "One Plus Grade 11"
GRADE_12_COURSE_NAME = "One Plus Grade 12"
GRADE_10_OPEN_CLASS_NAME = "Grade 10 - Open Class"
GRADE_11_OPEN_CLASS_NAME = "Grade 11 - Open Class"
GRADE_12_OPEN_CLASS_NAME = "Grade 12 - Open Class"
OPEN_SCHOOL = "Open School"

MAX_LEVEL = 7

# Social media
SOCIAL_MEDIA_ACTIVE = True
FB_APP_NUM = os.environ.get('FB_APP_NUM', '857396421078390')
FB_REDIRECT = os.environ.get('FB_REDIRECT', 'https://dig-it.me')
FB_SITE_TITLE = os.environ.get('FB_SITE_TITLE', 'dig-it')
FB_SITE_DESC = os.environ.get(
    'FB_SITE_DESC',
    'Challenge your maths skills and improve your marks. '
    'dig-it helps Gr10 - 12s score in maths - and in life.')

# Progressive Web App
PWA_SERVICE_WORKER_PATH = os.path.join(ENV_PATH, 'serviceworker.js')
PWA_APP_NAME = 'dig-it'
PWA_APP_DESCRIPTION = 'dig-it is a mobisite designed to support Grade 10 - Grade 12 maths learners.'
PWA_APP_THEME_COLOR = '#68baa7'
PWA_APP_ICONS = [
    {
        "src": "/media/img/appicons/dig-it_icon_96.png",
        "sizes": "96x96",
        "type": "image/png"
    },
    {
        "src": "/media/img/appicons/dig-it_icon_144.png",
        "sizes": "144x144",
        "type": "image/png"
    },
    {
        "src": "/media/img/appicons/dig-it_icon_192.png",
        "sizes": "192x192",
        "type": "image/png"
    }
]

try:
    from local_settings import *
except ImportError as e:
    pass
