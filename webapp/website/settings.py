# Django settings for website project.

from common.settings import *

# Avoid absolute paths by making them relative to this directory
import os
basedir = os.path.dirname(os.path.realpath(__file__))

# Use dedicated Redis test db for running test cases
TEST_RUNNER = 'website.utils.RedisTestSuiteRunner'

REDIS = {
    'host': 'redis',
    'port': 6379,
    'db': 0,
    'password': None,
    'decode_responses': True,
}

# Number of seconds to wait for Redis before giving up
REDIS_TIMEOUT = 45

SITE_ID = 1

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(basedir, 'static')

STATICFILES_DIRS += (os.path.join(basedir, 'custom-static'),)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'website.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'website.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    'registration',
    'cookielaw',

    # Forum (we share user profile models)
    'django_messages',
    'pagination',
    'djangobb_forum',
#    'haystack',

    # jammr code
    'website.jammr',
    'website.api',
    'website.recorded_jams',
    'website.payments',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGIN_REDIRECT_URL = '/profiles/edit/'

LOGGING['loggers']['website'] = {
    'handlers': ['console', 'mail_admins'],
    'level': 'DEBUG',
    'propagate': True,
}

ACCOUNT_ACTIVATION_DAYS = 60

RECAPTCHA_SECRET = os.environ.get('RECAPTCHA_SECRET')
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')

STRIPE_WEBHOOK_NAME = os.environ.get('STRIPE_WEBHOOK_NAME')
if os.environ.get('STRIPE_DEV_MODE', 'true').lower() == 'true':
    STRIPE_PUB_KEY = os.environ.get('STRIPE_DEV_PUB_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_DEV_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_DEV_WEBHOOK_SECRET')
else:
    STRIPE_PUB_KEY = os.environ.get('STRIPE_PROD_PUB_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_PROD_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_PROD_WEBHOOK_SECRET')
