"""
Django settings for cheapdrive_website project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

print(BASE_DIR)
# Quick-origin development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/




ALLOWED_HOSTS = []

import environ
# Initialise environment variables
env = environ.Env(DEBUG=(bool, False))
env_file = os.path.join(BASE_DIR.parent, '.env')

env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'entry',
    'refill',
    'cache',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cheapdrive_website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add this line
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

WSGI_APPLICATION = 'cheapdrive_website.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # Use PostGIS for geospatial support
        'HOST': 'localhost',           # Database host (localhost for local setup)
        'PORT': '5432', 
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),

    }
    
}


AUTH_USER_MODEL = 'entry.User'



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True

LOGIN_URL = '/login/'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR.parent, 'static\\')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), 
]
SESSION_COOKIE_AGE = int(env('SESSION_COOKIE_AGE'))
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
import os
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
os.environ['GDAL_INCLUDE_DIR'] = env('GDAL_INCLUDE_DIR', default="")
GDAL_LIBRARY_PATH = env('GDAL_LIBRARY_PATH',default="")

GEOS_LIBRARY_PATH = env('GEOS_LIBRARY_PATH',default="")


LOGGING_DIR = os.path.join(BASE_DIR, "logs")  # Create logs directory
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} - {name} - {levelname} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        # Console handler for development and debugging purposes.
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # File handler to log exceptions at the ERROR level.
        "exception_file": {
            "level": "ERROR",  
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "exception.log"),
            "formatter": "verbose",
        },
        "django_debug_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "django_debug.log"),
            "formatter": "verbose",
        },
        "debug_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "debug.log"),
            "formatter": "verbose",
        },
        "info_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "info.log"),
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "error.log"),
            "formatter": "verbose",
        },
        "warning_file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "warning.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
                "django_debug_file",
                "info_file",
                "error_file",
                "warning_file",
                "exception_file"
            ],
            "level": "DEBUG",
            "propagate": True,
        },
        "my_logger": {
            "handlers": [
                "console",
                "debug_file",
                "info_file",
                "error_file",
                "warning_file",
                "exception_file"
            ],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}