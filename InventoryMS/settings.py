import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
#
DEBUG = True

ALLOWED_HOSTS = ['zbi-inventory-app-axfcfebbawe7abet.italynorth-01.azurewebsites.net', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://zbi-inventory-app-axfcfebbawe7abet.italynorth-01.azurewebsites.net/']

# SECURE_SSL_REDIRECT = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'phonenumber_field',
    'crispy_forms',
    'crispy_bootstrap5',
    'imagekit',
    'django_extensions',
    'django_filters',
    'django_tables2',

    'store.apps.StoreConfig',
    'accounts.apps.AccountsConfig',
    'transactions.apps.TransactionsConfig',
    'invoice.apps.InvoiceConfig',
    'bills.apps.BillsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'InventoryMS.urls'

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

WSGI_APPLICATION = 'InventoryMS.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# 3. DATABASE
# Tutaj robimy "sprytny" warunek.
# Jeśli Azure podstawił nam dane do bazy (czyli zmienna DB_HOST istnieje) -> Używamy Postgresa.
# Jeśli nie (jesteśmy w domu) -> Używamy SQLite.

DB_HOST = os.environ.get('AZURE_POSTGRESQL_HOST')
DB_NAME = os.environ.get('AZURE_POSTGRESQL_DATABASE')
DB_USER = os.environ.get('AZURE_POSTGRESQL_USERNAME')
DB_PASSWORD = os.environ.get('AZURE_POSTGRESQL_PASSWORD')

if DB_HOST:
    # Jesteśmy na Azure (Produkcja)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': '5432',
        }
    }
else:
    # Jesteśmy lokalnie (Development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LOGIN_URL = 'user-login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_URL = 'logout'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

#STATIC_URL = 'static/'
#STATICFILES_DIRS = [os.path.join(BASE_DIR,'static')
#]
#STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
#MEDIA_ROOT = os.path.join(BASE_DIR, 'static/images')
#MEDIA_URL = '/images/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

#DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
#CRISPY_TEMPLATE_PACK = "bootstrap5"


#SCM_DO_BUILD_DURING_DEPLOYMENT = True

#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_URL = 'static/'


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


MEDIA_URL = '/images/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'static/images')


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
