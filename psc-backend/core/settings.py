"""
Django settings for VIMS Inspection - PSC Backend.

Configuration per TECH_STACK.md and BACKEND_STRUCTURE.md
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the backend .env file when present.
load_dotenv(BASE_DIR / '.env')

# Monkey-patch mssql-django to support SQL Server 2025 (version 17)
# This is needed because mssql-django 1.6 doesn't recognize SQL Server 2025 yet
try:
    from mssql.base import DatabaseWrapper
    if 17 not in DatabaseWrapper._sql_server_versions:
        DatabaseWrapper._sql_server_versions[17] = 2025
except ImportError:
    pass

# =============================================================================
# CORE SETTINGS
# =============================================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'modules.orb.orb',
    'modules.circular.circular',
    'modules.circular.circular_office',
    'modules.circular.circular_ship',
    # PSC module apps
    'apps.accounts',
    'apps.masters',
    'apps.inspection',
    'apps.car',
    'apps.sync',
    'apps.notifications',
    'apps.safety',
    'apps.certs',
    'apps.help_assistant',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# =============================================================================
# DATABASE (SQL Server)
# Per TECH_STACK.md Section 3
# =============================================================================
_db_name = os.getenv("DB_NAME", "ksm_marine_live")
_db_host = os.getenv("DB_HOST", "localhost")
_db_port = os.getenv("DB_PORT", "1433")
_db_user = os.getenv("DB_USER", "").strip()
_db_password = os.getenv("DB_PASSWORD", "")
_db_driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
_db_encrypt = os.getenv("DB_ENCRYPT", "no")
_db_trust_server_certificate = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
_db_trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "yes")

_db_extra_params = (
    f"Encrypt={_db_encrypt};"
    f"TrustServerCertificate={_db_trust_server_certificate};"
)
if _db_trusted_connection.lower() in ("true", "1", "yes") and not _db_user and not _db_password:
    _db_extra_params += "Trusted_Connection=yes;"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "mssql"),
        "NAME": _db_name,
        "HOST": _db_host,
        "PORT": _db_port,
        "USER": _db_user,
        "PASSWORD": _db_password,
        "OPTIONS": {
            "driver": _db_driver,
            "extra_params": _db_extra_params,
        },
    }
}




# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

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


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

# =============================================================================
# MEDIA FILES (user uploads: evidence, company logo, etc.)
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Company logo path (used in PDF report generation)
COMPANY_LOGO_PATH = MEDIA_ROOT / 'company' / 'logo.png'


# =============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# REST FRAMEWORK
# Per BACKEND_STRUCTURE.md
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.backends.PSCJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}


# =============================================================================
# JWT AUTHENTICATION
# Per TECH_STACK.md Section 7.3
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 60))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        minutes=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 43200))
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# =============================================================================
# CORS
# Per TECH_STACK.md Section 7.2
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000'
    ).split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# =============================================================================
# FILE UPLOAD
# Per TECH_STACK.md Section 4.2
# =============================================================================

UPLOAD_BASE_PATH = BASE_DIR / os.getenv("UPLOAD_BASE_PATH", "uploads")

MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 3))

# Allowed file types for evidence uploads
ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg']
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.jpg', '.jpeg']


# =============================================================================
# AUTHENTICATION BACKENDS
# Custom backend for PSC module authentication against existing tables
# =============================================================================

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.PSCAuthenticationBackend',
]

#==============================================================================
#EMAIL SETTINGS
#==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')

# Configure sender credentials through environment variables or psc-backend/.env.
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'pms@cymsol.co.in')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    f"KSM Marine <{EMAIL_HOST_USER}>",
)


# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps.accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
