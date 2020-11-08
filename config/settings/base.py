# Django settings for bordercore project.

import json
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

PROJECT_DIR = BASE_DIR / "bordercore"

sys.path.insert(0, str(PROJECT_DIR / "apps"))
sys.path.insert(0, str(PROJECT_DIR / "lib"))

# JSON-based secrets module
with open('{}/config/settings/secrets.json'.format(BASE_DIR)) as f:
    secrets = json.loads(f.read())


def get_secret(setting, secrets=secrets):
    '''Get the secret variable or return explicit exception.'''
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {0} environment variable'.format(setting)
        raise ImproperlyConfigured(error_msg)


ADMINS = (
    ('F. Jerrell Schivers', 'jerrell@bordercore.com'),
)

MANAGERS = ADMINS

# Set this so we can read it later in some code shared between
#  Django and a lambda. In the lambda we don't have access to any
#  Django modules, and thus can't get in the usual way by
#  importing settings from django.conf. So use the environment
#  instead.
os.environ["DATABASE_PASSWORD"] = get_secret('DATABASE_PASSWORD')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bordercore',
        'USER': 'bordercore',
        'PASSWORD': get_secret('DATABASE_PASSWORD'),
        'HOST': 'bordercore.cvkm90zuldto.us-east-1.rds.amazonaws.com',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'US/Eastern'

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

FILE_UPLOAD_PERMISSIONS = 0o664

# Make this unique, and don't share it with anybody.
SECRET_KEY = get_secret('SECRET_KEY')

for env in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_ASSOCIATE_TAG'):
    os.environ[env] = get_secret(env)

USE_S3 = True
AWS_STORAGE_BUCKET_NAME = "bordercore-blobs"
AWS_BUCKET_NAME_MUSIC = "bordercore-music"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_LOCATION = "django"

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Set this to silence S3Boto3Storage warning
AWS_DEFAULT_ACL = None

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# STATIC_URL = '/static/'
STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_LOCATION}/'

# Additional locations of static files
STATICFILES_DIRS = (
    str(PROJECT_DIR / "static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = 'blobs'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'
COVER_URL = 'https://blobs.bordercore.com/'
MEDIA_URL_MUSIC = f'https://{AWS_BUCKET_NAME_MUSIC}.s3.amazonaws.com/'

ROOT_URLCONF = 'config.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'config.wsgi.application'

ALLOWED_HOSTS = ('localhost', 'www.bordercore.com', 'bordercore.com', 'beta.bordercore.com', '10.3.2.2', '136.31.25.50', '72.55.156.170')

INSTALLED_APPS = (

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'accounts',
    'blob',
    'book',
    'collection',
    'contact',
    'drill',
    'feed',
    'fitness',
    'lib',
    'node',
    'tag',
    'bookmark',
    'music',
    'pygments',
    'quote',
    'rest_framework',
    'rest_framework.authtoken',
    'storages',
    'todo'

)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'PAGE_SIZE': 50
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(PROJECT_DIR / "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'context_processors.get_counts'
            ]
        },
    },
]

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

LOGIN_URL = "/accounts/login/"

# Elasticsearch config
# See dev.py and prod.py for endpoint url
ELASTICSEARCH_INDEX = "bordercore"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'bordercore': {
            'handlers': ['bordercore'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
