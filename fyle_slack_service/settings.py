"""
Django settings for slack project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import sys
import os
from pathlib import Path

from fyle_slack_service.sentry import Sentry


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEBUG') == 'True' else False

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'fyle_slack_app',
    'django_q'
]

MIDDLEWARE = [
    'fyle_slack_service.exception_middleware.CustomExceptionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fyle_slack_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fyle_slack_service.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    },
    # Cache DB
    'cache': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'cache.db.sqlite3'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'slack_cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

DATABASE_ROUTERS = ['fyle_slack_service.cache_router.CacheRouter']

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'


Q_CLUSTER = {
    'name': 'fyle_slack_service',
    'compress': True,
    'save_limit': 0,
    'workers': 4,
    'queue_limit': 50,
    'orm': 'default',
    'ack_failures': True,
    'max_attempts': 1,
    'attempt_count': 1,
    'retry': 14400,
    'timeout': 3600,
    'catch_up': False,
    'poll': 1
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '{levelname} %s {asctime} {module} {message} ' % 'fyle-slack-service',
            'style': '{',
        },
        'requests': {
            'format': 'request {levelname} %s {message}' % 'fyle-slack-service',
            'style': '{'
        }
    },
    'handlers': {
        'debug_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        },
        'request_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'requests'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['request_logs'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['request_logs'],
            'propagate': False
        },
        'fyle_slack_service': {
            'handlers': ['debug_logs'],
            'level': 'ERROR',
            'propagate': False
        },
        'fyle_slack_app': {
            'handlers': ['debug_logs'],
            'level': 'ERROR',
            'propagate': False
        },
        'gunicorn': {
            'handlers': ['request_logs'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

LOG_LEVEL = os.environ.get('LOGGING_LEVEL', 'DEBUG')

# Fyle Settings
FYLE_APP_URL = os.environ['FYLE_APP_URL']
FYLE_ACCOUNTS_URL = os.environ['FYLE_ACCOUNTS_URL']
FYLE_CLIENT_ID = os.environ['FYLE_CLIENT_ID']
FYLE_CLIENT_SECRET = os.environ['FYLE_CLIENT_SECRET']
FYLE_SLACK_APP_MIXPANEL_TOKEN = os.environ['FYLE_SLACK_APP_MIXPANEL_TOKEN']
FYLE_BRANCHIO_BASE_URI = os.environ['FYLE_BRANCHIO_BASE_URI']

# Slack Settings
SLACK_CLIENT_ID = os.environ['SLACK_CLIENT_ID']
SLACK_CLIENT_SECRET = os.environ['SLACK_CLIENT_SECRET']
SLACK_APP_ID = os.environ['SLACK_APP_ID']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
SLACK_SERVICE_BASE_URL = os.environ['SLACK_SERVICE_BASE_URL']

# Sentry Integration
SENTRY_DSN = os.environ.get('SENTRY_DSN')
ENVIRONMENT = os.environ.get('ENVIRONMENT')

# Initialising sentry integration
Sentry.init()

# Test Settings
FYLE_TOKEN_URI = os.environ.get('FYLE_TOKEN_URI', None)
FYLE_REFRESH_TOKEN = os.environ.get('FYLE_REFRESH_TOKEN', None)
FYLE_SERVER_URL = os.environ.get('FYLE_SERVER_URL', None)
