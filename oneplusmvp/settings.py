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
    os.path.join(BASE_DIR, "templates"),
]

BASE_URL = 'oneplus.qa.praekeltfoundation.org'
# os.path.join(BASE_DIR, "oneplus/templates")

ALLOWED_HOSTS = ['*']

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
)
# Application definition

SITE_ID = 1

INSTALLED_APPS = (
    #"django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "grappelli",
    "mobileu",
    "import_export",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "oneplus",
    "core",
    "gamification",
    "communication",
    "content",
    "auth",
    "djcelery",
    "organisation",
    "django_summernote",
    "south",
    "django_bleach",
    "bs4",
    "google_analytics",
    "raven.contrib.django.raven_compat",
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'oneplusmvp.urls'

WSGI_APPLICATION = 'oneplusmvp.wsgi.application'

# Close the session when user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

AUTH_USER_MODEL = "auth.CustomUser"

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

GOOGLE_ANALYTICS = {
    'google_analytics_id': 'UA-52417331-1',
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = abspath('media')

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

# Base url for vumi requests
VUMI_GO_BASE_URL = "http://go.vumi.org/api/v1/go/http_api_nostream"
VUMI_GO_CONVERSATION_KEY = "0bc156dc56c24c3fab5e63c92e09829f"
VUMI_GO_ACCOUNT_KEY = "b365f245538841a08586a29b5b568c6c"
VUMI_GO_ACCOUNT_TOKEN = "vaiToa6c"

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
ONEPLUS_WIN_REQUIRED = 9

# Airtime to win per week in Rands
ONEPLUS_WIN_AIRTIME = 5

GRAPPELLI_ADMIN_TITLE = "OnePlus Admin"

CELERY_IMPORTS = ('mobileu.tasks', 'communication.tasks')
BROKER_URL = 'amqp://guest:guest@localhost:5672/'
# The minimum number of SMSes that can be sent before being sent with celery
MIN_VUMI_CELERY_SEND = 1

FIXTURE_DIRS = (
    "/fixtures/",
    abspath('fixtures'),
)

USE_TZ = False

EMAIL_HOST = 'localhost'
EMAIL_PORT = '25'
SERVER_EMAIL = 'info@oneplus.co.za'
EMAIL_SUBJECT_PREFIX = '[ONE-PLUS] '
MANAGERS = (
    ('Jane', 'info@oneplus.co.za'),
)
try:
    from local_settings import *
except ImportError as e:
    pass
