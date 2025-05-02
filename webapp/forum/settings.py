# Django settings for forum project.

# Avoid absolute paths by making them relative to this directory
import os
basedir = os.path.dirname(os.path.realpath(__file__))

from common.settings import *

SITE_ID = 2

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(basedir, 'static')

STATICFILES_DIRS += (os.path.join(basedir, 'custom-static'),)

MEDIA_ROOT = os.path.join(basedir, 'media')

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'djangobb_forum.middleware.LastLoginMiddleware',
    'djangobb_forum.middleware.UsersOnline',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'forum.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'forum.wsgi.application'

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

    # Forum
    'django_messages',
    'pagination',
    'djangobb_forum',
    'haystack',

    'forum.email_notifications',
    'forum.add_topic',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(basedir, 'templates')],
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
                'djangobb_forum.context_processors.forum_settings',
            ]
        },
    },
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(basedir, 'djangobb_index'),
        'INCLUDE_SPELLING': False,
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# DjangoBB settings
DJANGOBB_FORUM_BASE_TITLE = 'jammr Forum'
DJANGOBB_HEADER = 'jammr Forum'
DJANGOBB_TAGLINE = 'Home of the jammr Community'
DJANGOBB_ATTACHMENT_SIZE_LIMIT = 10 * 1024 * 1024

LOGIN_REDIRECT_URL = '/' # back to forum index upon login
