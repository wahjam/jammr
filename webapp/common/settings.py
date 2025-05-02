# Django settings for website project.

import os

ADMINS = (
    ('Stefan Hajnoczi', 'stefanha@jammr.net'),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'jammr.net <info@jammr.net>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
if os.environ.get('SEND_EMAIL', '').lower() == 'false':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# The SMTP server hostname
EMAIL_HOST = 'exim4'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'website',                      # Or path to database file if using sqlite3.
        'USER': 'website',                      # Not used with sqlite3.
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'), # Not used with sqlite3.
        'HOST': 'postgres',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
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
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Share session cookie across subdomains
SESSION_COOKIE_DOMAIN = '.jammr.net'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'NOTSET',
            'filters': [],
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'gunicorn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'class': 'logging.Formatter',
        }
    }
}

FILE_UPLOAD_PERMISSIONS = 0o644

ALLOWED_HOSTS = [
    '.jammr.net',  # all subdomains and FQDNs
    '.jammr.net.',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

# Only allow cookies over HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'common.auth_backend.EmailModelBackend'
]

GEOIP_PATH = '/usr/share/GeoIP'
