"""
Django settings for oneplusmvp project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '2*pv1ow5a6l^+h&ea#jy63#k4hw&lo2b_wy+9d+^_c#sce0at5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = [os.path.join(BASE_DIR, "templates")] # os.path.join(BASE_DIR, "oneplus/templates")

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    #"django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "grappelli",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "oneplus",
    "core",
    "gamification",
    "communication",
    "content",
    "auth",
    "organisation",
    "django_summernote",
    "south"
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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = "/static/"

MEDIA_ROOT = "/media/"
MEDIA_URL = "/media/"

# The number of correct answers in a week required to win airtime
ONEPLUS_WIN_REQUIRED = 9

# Airtime to win per week in Rands
ONEPLUS_WIN_AIRTIME = 5

GRAPPELLI_ADMIN_TITLE = "OnePlus Admin"

FIXTURE_DIRS = (
   "/fixtures/",
)
