from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'elasticapm.contrib.django',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.users',
    'apps.patients',
    'apps.appointments',
    'apps.records',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'elasticapm.contrib.django.middleware.TracingMiddleware',
    'core.middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='pulse_care'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('PAGE_SIZE', default=20, cast=int),
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=config('JWT_ACCESS_HOURS', default=8, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

API_VERSION = '1.0.0'
API_VERSION_PREFIX = f'v{API_VERSION.split(".")[0]}'  # e.g. "v1"

SPECTACULAR_SETTINGS = {
    'TITLE': 'PulseCare API',
    'DESCRIPTION': (
        'REST API for PulseCare — a healthcare management system that handles '
        'patients, appointments, medical records, and staff users.'
    ),
    'VERSION': API_VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {'name': 'PulseCare Team', 'email': 'dev@pulsecare.com'},
    'LICENSE': {'name': 'MIT'},
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SECURITY': [{'BearerAuth': []}],
    'SECURITY_DEFINITIONS': {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    },
    'TAGS': [
        {'name': 'Accounts', 'description': 'Registration and password reset'},
        {'name': 'Auth', 'description': 'JWT token endpoints'},
        {'name': 'Users', 'description': 'Staff user management'},
        {'name': 'Patients', 'description': 'Patient registration and management'},
        {'name': 'Appointments', 'description': 'Appointment scheduling'},
        {'name': 'Records', 'description': 'Medical records and attachments'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENUM_GENERATE_CHOICE_DESCRIPTION': True,
}

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:5173',
).split(',')
CORS_ALLOW_CREDENTIALS = True

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='django-db')
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = config('CELERY_TASK_TIME_LIMIT', default=1800, cast=int)
CELERY_TASK_SOFT_TIME_LIMIT = config('CELERY_TASK_SOFT_TIME_LIMIT', default=1500, cast=int)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

APPOINTMENT_REMINDER_HOURS_BEFORE = config('APPOINTMENT_REMINDER_HOURS_BEFORE', default=24, cast=int)
PASSWORD_RESET_OTP_TTL_SECONDS = config('PASSWORD_RESET_OTP_TTL_SECONDS', default=300, cast=int)
PASSWORD_RESET_OTP_RESEND_SECONDS = config('PASSWORD_RESET_OTP_RESEND_SECONDS', default=60, cast=int)
PASSWORD_RESET_OTP_MAX_ATTEMPTS = config('PASSWORD_RESET_OTP_MAX_ATTEMPTS', default=5, cast=int)

ELASTIC_APM = {
    'SERVICE_NAME': config('APM_SERVICE_NAME', default='pulse-care-api'),
    'ENVIRONMENT': config('APM_ENVIRONMENT', default='development'),
    'SECRET_TOKEN': config('APM_SECRET_TOKEN', default=''),
    'SERVER_URL': config('APM_SERVER_URL', default='http://localhost:8200'),
    'DEBUG': DEBUG,
    'CAPTURE_BODY': 'errors',
    'CAPTURE_HEADERS': True,
    'TRANSACTION_SAMPLE_RATE': config('APM_SAMPLE_RATE', default=1.0, cast=float),
    'DJANGO_TRANSACTION_NAME_FROM_ROUTE': True,
}

LOG_LEVEL = config('LOG_LEVEL', default='INFO')
CELERY_LOG_LEVEL = config('CELERY_LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {process:d} {thread:d} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{asctime}] {levelname} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'elasticapm': {
            'level': 'INFO',
            'class': 'elasticapm.contrib.django.handlers.LoggingHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console',],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'elasticapm'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'elasticapm'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.requests': {
            'handlers': ['console', 'elasticapm'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console', 'elasticapm'],
            'level': CELERY_LOG_LEVEL,
            'propagate': False,
        },
    },
}
