import sys
from pathlib import Path

# 1. Правильное определение BASE_DIR для EXE и обычного запуска
if getattr(sys, 'frozen', False):
    # Если запущено из .exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Обычный запуск через python
    BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Папка для отчетов и БД должна быть в ДОСТУПНОМ для записи месте!
# Например, в папке "Документы" пользователя или в AppData
# USER_DATA_DIR = Path.home() / "NSPD_App_Data"
# USER_DATA_DIR.mkdir(exist_ok=True)
#
# REPORTS_DIR = USER_DATA_DIR / "reports"
# REPORTS_DIR.mkdir(exist_ok=True)

SECRET_KEY = 'django-insecure-nspd-dev-only-change-in-production'

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.vercel.app',
]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'analyzer',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'nspd_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Убедитесь, что папка templates лежит рядом с .exe
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'nspd_site.wsgi.application'

DATABASES = {}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / 'analyzer' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REPORTS_DIR = BASE_DIR / 'reports'
