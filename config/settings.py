"""Django settings for the Personal DevOS modular monolith."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DJANGO_DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='development-only-secret-key')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])
if not DEBUG:
    # Caddy terminates HTTPS and forwards X-Forwarded-Proto to gunicorn.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sites', 'accounts', 'activity', 'coding', 'blog',
    'integrations', 'common', 'allauth', 'allauth.account', 'allauth.socialaccount',
    'allauth.socialaccount.providers.kakao',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:home'
LOGIN_URL = 'auth:login'
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.PrivacyFirstSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {'kakao': {'APPS': [{
    'client_id': env('KAKAO_REST_API_KEY', default=''),
    'secret': env('KAKAO_CLIENT_SECRET', default=''), 'key': '',
}]}}

# Live integrations are implemented in later milestones.
GITHUB_WEBHOOK_SECRET = env('GITHUB_WEBHOOK_SECRET', default='')
GITHUB_ACCESS_TOKEN = env('GITHUB_ACCESS_TOKEN', default='')
GITHUB_ALLOWED_REPOSITORIES = env.list('GITHUB_ALLOWED_REPOSITORIES', default=[])
POST_SOURCE_EXTENSIONS = env.list(
    'POST_SOURCE_EXTENSIONS',
    default=['.py', '.java', '.cpp', '.c', '.cc', '.js', '.ts', '.go', '.kt', '.rb'],
)
LLM_PROVIDER = env('LLM_PROVIDER', default='')
LLM_MODEL = env('LLM_MODEL', default='')
LLM_API_KEY = env('LLM_API_KEY', default='')
LLM_TIMEOUT_SECONDS = env.int('LLM_TIMEOUT_SECONDS', default=60)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
# Results live in PostgreSQL (ProcessingRun); no Celery result store, even if one is configured.
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool('CELERY_TASK_EAGER_PROPAGATES', default=True)

DATABASES = {'default': env.db(
    'DATABASE_URL',
    default='postgres://postgres:postgres@127.0.0.1:5432/personal_dev_os',
)}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
