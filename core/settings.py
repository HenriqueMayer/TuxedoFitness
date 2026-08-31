import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = Path(os.environ.get('TUXEDO_ENV_FILE', BASE_DIR / '.env'))
load_dotenv(ENV_FILE, override=False)


def env_flag(name, default=False):
    value = os.environ.get(name, str(default))
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def local_path(name, default):
    path = Path(os.environ.get(name, default))
    return path if path.is_absolute() else BASE_DIR / path


SECRET_KEY = os.environ.get('SECRET_KEY', '').strip()
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY must be set in the environment.')

DEBUG = env_flag('DEBUG', False)
ALLOW_SIGNUPS = env_flag('ALLOW_SIGNUPS', False)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver'
    ).split(',')
    if host.strip()
]

DATA_DIR = local_path('TUXEDO_DATA_DIR', 'var/private')
DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
if os.name == 'posix':
    DATA_DIR.chmod(0o700)
DATABASE_PATH = local_path(
    'TUXEDO_FITNESS_DB', DATA_DIR / 'tuxedo-fitness.sqlite3'
)

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages',
    'accounts',
    'integrations',
    'training',
    'analytics',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.application_state',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_PATH,
        'OPTIONS': {
            'init_command': 'PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;',
            'timeout': 20,
            'transaction_mode': 'IMMEDIATE',
        },
    }
}

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

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static', BASE_DIR / 'assets']
STATIC_ROOT = BASE_DIR / 'var' / 'static'

SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF],
    'script-src-attr': [CSP.NONE],
    'style-src': [CSP.SELF],
    'font-src': [CSP.SELF],
    'img-src': [CSP.SELF, 'data:'],
    'connect-src': [CSP.SELF],
    'manifest-src': [CSP.SELF],
    'media-src': [CSP.SELF],
    'worker-src': [CSP.SELF],
    'object-src': [CSP.NONE],
    'base-uri': [CSP.SELF],
    'form-action': [CSP.SELF],
    'frame-src': [CSP.NONE],
    'frame-ancestors': [CSP.NONE],
}

HTTPS = env_flag('HTTPS')
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS
SECURE_SSL_REDIRECT = HTTPS
SECURE_HSTS_SECONDS = 31536000 if HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = HTTPS
SECURE_HSTS_PRELOAD = HTTPS
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

if HTTPS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'pages:landing'

SYNC_LOCK_STALE_SECONDS = int(os.environ.get('SYNC_LOCK_STALE_SECONDS', '21600'))
if SYNC_LOCK_STALE_SECONDS < 60:
    raise ImproperlyConfigured('SYNC_LOCK_STALE_SECONDS must be at least 60.')
