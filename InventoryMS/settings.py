"""
Django settings for InventoryMS.

All environment specific values are read from environment variables (a local
.env file is loaded automatically in development). See .env.example.
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    raw = os.environ.get(name, default)
    return [part.strip() for part in raw.split(',') if part.strip()]


# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
DEBUG = env_bool('DEBUG', default=False)

# True while running "manage.py test". Tests talk plain HTTP to an
# un-collected static tree, so the HTTPS redirect and the manifest static
# storage are switched off for them (see below), whatever DEBUG is.
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        # Development only. Never used when DEBUG is off.
        SECRET_KEY = 'django-insecure-dev-only-key-change-me'
    else:
        raise ImproperlyConfigured(
            'SECRET_KEY environment variable is required when DEBUG is off.'
        )

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

# Full origins including scheme, e.g. https://inventory.example.com
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

# Azure App Service sets WEBSITE_HOSTNAME automatically.
_azure_host = os.environ.get('WEBSITE_HOSTNAME')
if _azure_host:
    if _azure_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_azure_host)
    if f'https://{_azure_host}' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f'https://{_azure_host}')

# Self sign-up. New accounts stay inactive until an admin approves them.
ALLOW_REGISTRATION = env_bool('ALLOW_REGISTRATION', default=True)

# Login throttling: lock a username/IP pair after this many failures.
LOGIN_MAX_ATTEMPTS = int(os.environ.get('LOGIN_MAX_ATTEMPTS', '5'))
LOGIN_LOCKOUT_SECONDS = int(os.environ.get('LOGIN_LOCKOUT_SECONDS', '900'))

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

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
    'accounts.middleware.ActiveProfileMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'InventoryMS.middleware.SecurityHeadersMiddleware',
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
                'InventoryMS.context_processors.business',
                'accounts.context_processors.roles',
            ],
        },
    },
]

WSGI_APPLICATION = 'InventoryMS.wsgi.application'

# ---------------------------------------------------------------------------
# Database: PostgreSQL when configured, SQLite for local development.
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get('AZURE_POSTGRESQL_HOST') or os.environ.get('DB_HOST')

if DB_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('AZURE_POSTGRESQL_DATABASE') or os.environ.get('DB_NAME'),
            'USER': os.environ.get('AZURE_POSTGRESQL_USERNAME') or os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('AZURE_POSTGRESQL_PASSWORD') or os.environ.get('DB_PASSWORD'),
            'HOST': DB_HOST,
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {'sslmode': os.environ.get('DB_SSLMODE', 'prefer')},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            # SQLITE_PATH lets containers keep the database on a volume.
            'NAME': os.environ.get('SQLITE_PATH') or BASE_DIR / 'db.sqlite3',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'user-login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'user-login'

SESSION_COOKIE_AGE = int(os.environ.get('SESSION_COOKIE_AGE', str(60 * 60 * 12)))

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('TIME_ZONE', 'Africa/Nairobi')
USE_I18N = True
USE_TZ = True

PHONENUMBER_DEFAULT_REGION = os.environ.get('PHONENUMBER_DEFAULT_REGION', 'KE')

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Kept at static/images so existing uploaded profile pictures keep working.
MEDIA_URL = '/images/'
MEDIA_ROOT = BASE_DIR / 'static' / 'images'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG or TESTING else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

# Static files are only used by our own pages, so no wildcard CORS header.
WHITENOISE_ALLOW_ALL_ORIGINS = False

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ---------------------------------------------------------------------------
# Business details printed on receipts and invoices
# ---------------------------------------------------------------------------
BUSINESS = {
    'name': os.environ.get('BUSINESS_NAME', 'InventoryMS'),
    'address': os.environ.get('BUSINESS_ADDRESS', 'Tom Mboya Street, Tudor'),
    'po_box': os.environ.get('BUSINESS_PO_BOX', 'P.O. Box 90420-80100, Mombasa'),
    'phone': os.environ.get('BUSINESS_PHONE', '+254 700 000000'),
    'email': os.environ.get('BUSINESS_EMAIL', ''),
    'tax_pin': os.environ.get('BUSINESS_TAX_PIN', ''),
    'currency': os.environ.get('BUSINESS_CURRENCY', 'Ksh'),
}

# ---------------------------------------------------------------------------
# Loyalty programme
#   earn_per:     spend (after discounts, before tax) needed to earn 1 point
#   point_value:  money value of 1 point when redeemed at checkout
#   min_redeem:   smallest number of points that can be redeemed at once
# ---------------------------------------------------------------------------
LOYALTY = {
    'enabled': env_bool('LOYALTY_ENABLED', default=True),
    'earn_per': os.environ.get('LOYALTY_EARN_PER', '100'),
    'point_value': os.environ.get('LOYALTY_POINT_VALUE', '1.00'),
    'min_redeem': int(os.environ.get('LOYALTY_MIN_REDEEM', '0')),
}

# ---------------------------------------------------------------------------
# Production hardening
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', default=not TESTING)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_HTTPONLY = True
# Page scripts read the token from the form field, never from the cookie.
CSRF_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Browser security headers (InventoryMS.middleware.SecurityHeadersMiddleware)
# Scripts and styles only from this site and the pinned CDNs (all with SRI
# hashes). No inline scripts, styles or style attributes anywhere.
# ---------------------------------------------------------------------------
CONTENT_SECURITY_POLICY = os.environ.get('CONTENT_SECURITY_POLICY', '; '.join([
    "default-src 'self'",
    "script-src 'self' https://cdn.jsdelivr.net https://code.jquery.com",
    "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
    "font-src 'self' https://cdnjs.cloudflare.com",
    "img-src 'self' data:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
]))
PERMISSIONS_POLICY = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
CROSS_ORIGIN_EMBEDDER_POLICY = os.environ.get('CROSS_ORIGIN_EMBEDDER_POLICY', 'require-corp')
CROSS_ORIGIN_RESOURCE_POLICY = 'same-origin'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': os.environ.get('LOG_LEVEL', 'INFO')},
    'loggers': {
        'weasyprint': {'level': 'ERROR'},
        'fontTools': {'level': 'ERROR'},
    },
}
