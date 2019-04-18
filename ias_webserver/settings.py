"""
Django settings for ias_webserver project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import logging.config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'mb$ip=bi%m*kstsge)7@$=o+-q-nq#qt6-9k09v)lda(s#&td4'
)
# SECURITY WARNING: don't run with debug turned on in production!
if (os.getenv('SECRET_KEY', False)):
    DEBUG = False
else:
    DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'dry_rest_permissions',
    'corsheaders',
    'alarms.apps.AlarmConfig',
    'cdb',
    'panels',
    'tickets',
    'timers',
    'users'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # should be at the beginning
    'django.middleware.security.SecurityMiddleware',
    'users.middleware.GetTokenMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ias_webserver.urls'

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

WSGI_APPLICATION = 'ias_webserver.wsgi.application'

# CORS Configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# CORS_ORIGIN_WHITELIST = (
#     '<DOMAIN>[:PORT]',
# )

# Disable Django's logging setup
LOGGING_CONFIG = None

LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
IAS_LOGS_FOLDER = os.getenv('IAS_LOGS_FOLDER', 'logs/')

if not os.environ.get('TESTING', False):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'custom': {
                '()': 'utils.logging.iasFormatter',
                'format': '{asctime} |{levelname}| [{name}] [{filename}:{lineno}] [{threadName}] {message}',
                'style': '{',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'custom'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5,
                'filename': IAS_LOGS_FOLDER + '/webserver.log',
                'formatter': 'custom'
            },
        },
        'loggers': {
            '': {
                'level': LOG_LEVEL,
                'handlers': ['console'],
                'propagate': True
            },
            'alarms': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'cdb': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'panels': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'tickets': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file'],
                'propagate': False,
            },
        },
    })

# Database
DATABASE_ROUTERS = ['cdb.routers.CdbRouter']

if os.environ.get('DB_ENGINE') == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'IntegratedAlarmSystem'),
            'USER': os.getenv('DB_USER', 'ias'),
            'HOST': os.getenv('DB_HOST', 'database'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'PASSWORD': os.getenv('DB_PASS', 'ias')
        }
    }
elif os.environ.get('DB_ENGINE') == 'oracle':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.oracle',
            'NAME': "{}:{}/{}".format(
                os.getenv('DB_HOST', 'database'),
                os.getenv('DB_PORT', '1521'),
                os.getenv('DB_NAME', 'IntegratedAlarmSystem')
            ),
            'USER': os.getenv('DB_USER', 'ias'),
            'PASSWORD': os.getenv('DB_PASS', 'ias')
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.' +
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password for other processes
PROCESS_CONNECTION_PASS = os.environ.get('PROCESS_CONNECTION_PASS', 'dev_pass')


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Channel Layers:
if os.environ.get('REDIS_HOST', False):
    CHANNEL_LAYERS = {
        "default": {
            # This example app uses the Redis channel layer
            # implementation asgi_redis
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(os.environ.get('REDIS_HOST', False), 6379)],
            }
        },
    }

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

ASGI_APPLICATION = "ias_webserver.routing.application"

BROADCAST_RATE_FACTOR = 2
BROADCAST_RATE = 10
NOTIFICATIONS_RATE = 0.5
BROADCAST_THRESHOLD = 11
UNSHELVE_CHECKING_RATE = 60
FILES_LOCATION = "private_files"
TEST_FILES_LOCATION = "panels/tests/private_files/"
CDB_LOCATION = "CDB/"
TEST_CDB_LOCATION = "cdb/tests/CDB/"
IAS_FILE = "ias.json"
IASIOS_FILE = "IASIO/iasios.json"
SUPERVISORS_FOLDER = "Supervisor/"
DASUS_FOLDER = "DASU/"
TEMPLATES_FILE = "TEMPLATE/templates.json"
