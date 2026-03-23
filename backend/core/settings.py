"""
========================================================
  ФАЙЛ: backend/settings.py
  НАЗНАЧЕНИЕ: Главный файл конфигурации Django-проекта.
  Здесь задаются все настройки: база данных, безопасность,
  установленные приложения, JWT и CORS.
========================================================
"""

import os
from pathlib import Path
from datetime import timedelta

# -----------------------------------------------------------
# BASE_DIR — абсолютный путь до корня проекта (папка backend/)
# Используется для построения путей к файлам внутри проекта
# -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------
# SECRET_KEY — секретный ключ Django для шифрования сессий,
# CSRF-токенов и других криптографических операций.
# ⚠️ КАК ПОЛУЧИТЬ: запустите команду в терминале:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Скопируйте результат и вставьте ниже вместо 'СГЕНЕРИРУЙТЕ_КЛЮЧ'
# В продакшене храните в переменной окружения, не в коде!
# -----------------------------------------------------------
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'mGpvKRSkydfUQz5ehI7rYjDMPpsY9VXz_f1DG4AYjxdcEytEENsI8c_Tw7xTEfTbUWM')


# -----------------------------------------------------------
# DEBUG — режим отладки.
# True  = показывать подробные ошибки (только при разработке!)
# False = скрывать ошибки от пользователя (продакшен)
# -----------------------------------------------------------
DEBUG = os.environ.get('DEBUG', 'True') == 'True'


# -----------------------------------------------------------
# ALLOWED_HOSTS — список доменов/IP, с которых разрешены запросы.
# При разработке оставьте как есть.
# ⚠️ В продакшене добавьте сюда ваш домен, например:
#   ['autoservice.ru', 'www.autoservice.ru', '185.123.45.67']
# -----------------------------------------------------------
ALLOWED_HOSTS = [
    'autoservice-production-91e0.up.railway.app',
    'localhost',
    '127.0.0.1',
]

# -----------------------------------------------------------
# INSTALLED_APPS — список всех подключённых Django-приложений.
# Порядок важен: django.contrib.* — встроенные,
# третьи стороны — corsheaders, rest_framework,
# наши приложения — api
# -----------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',        # Встроенная админ-панель Django
    'django.contrib.auth',         # Система аутентификации (пользователи, пароли)
    'django.contrib.contenttypes', # Нужно для связей между моделями
    'django.contrib.sessions',     # Хранение сессий
    'django.contrib.messages',     # Система сообщений (flash-уведомления)
    'django.contrib.staticfiles',  # Статические файлы (CSS, JS, изображения)

    # --- Сторонние библиотеки ---
    'corsheaders',                 # CORS: разрешает React обращаться к этому серверу
    'rest_framework',              # Django REST Framework — создание RESTful API
    'rest_framework_simplejwt',    # JWT-аутентификация (токены вместо сессий)

    # --- Наше приложение ---
    'api',                         # Основное приложение с моделями, видами, сериализаторами
]


# -----------------------------------------------------------
# MIDDLEWARE — цепочка обработчиков каждого HTTP-запроса.
# Запрос проходит сверху вниз, ответ — снизу вверх.
# CorsMiddleware ОБЯЗАН быть первым!
# -----------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',        # ← Первым! Иначе CORS не работает
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',    # Защита от CSRF-атак
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -----------------------------------------------------------
# ROOT_URLCONF — файл с главной таблицей маршрутов (URL)
# -----------------------------------------------------------
ROOT_URLCONF = 'core.urls'


# -----------------------------------------------------------
# TEMPLATES — настройки шаблонизатора Django (Jinja2-совместимый)
# Используется для HTML-страниц (в нашем случае — для админки)
# -----------------------------------------------------------
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


# -----------------------------------------------------------
# WSGI_APPLICATION — точка входа для WSGI-сервера (gunicorn и т.п.)
# -----------------------------------------------------------
WSGI_APPLICATION = 'core.wsgi.application'


# -----------------------------------------------------------
# DATABASES — настройки подключения к базе данных PostgreSQL.
# ⚠️ КАК НАСТРОИТЬ:
#   1. Установите PostgreSQL на компьютер (https://postgresql.org)
#   2. Запустите pgAdmin или psql
#   3. Создайте базу данных командой:
#      CREATE DATABASE autoservice_db;
#   4. Создайте пользователя (или используйте существующего postgres):
#      CREATE USER autoservice_user WITH PASSWORD 'ваш_пароль';
#      GRANT ALL PRIVILEGES ON DATABASE autoservice_db TO autoservice_user;
#   5. Вставьте имя БД, пользователя и пароль ниже
# -----------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Используем PostgreSQL
        'NAME': os.environ.get('DB_NAME', 'autoservice_db'),        # Имя базы данных (создайте в PostgreSQL)
        'USER': os.environ.get('DB_USER', 'postgres'),              # Имя пользователя PostgreSQL
        'PASSWORD': os.environ.get('DB_PASSWORD', '`12345`'), # Пароль пользователя
        'HOST': os.environ.get('DB_HOST', 'localhost'),             # Адрес сервера (localhost при локальной разработке)
        'PORT': os.environ.get('DB_PORT', '5432'),                  # Порт PostgreSQL (стандартный — 5432)
    }
}


# -----------------------------------------------------------
# AUTH_PASSWORD_VALIDATORS — правила сложности паролей.
# Django автоматически проверяет пароли при регистрации.
# -----------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},         # Минимум 8 символов
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},         # Не слишком простой
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},        # Не только цифры
]


# -----------------------------------------------------------
# Язык и временная зона
# -----------------------------------------------------------
LANGUAGE_CODE = 'ru-ru'   # Русский язык интерфейса
TIME_ZONE = 'Europe/Moscow'  # Московское время
USE_I18N = True            # Включить интернационализацию
USE_TZ = True              # Хранить даты в UTC, отображать в TIME_ZONE


# -----------------------------------------------------------
# STATIC_URL / MEDIA_URL — адреса для статики и загружаемых файлов
# -----------------------------------------------------------
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Папка для загружаемых файлов (аватары и т.п.)


# -----------------------------------------------------------
# DEFAULT_AUTO_FIELD — тип поля ID по умолчанию для всех моделей
# BigAutoField = 64-битный целочисленный ID (поддерживает >2 млрд записей)
# -----------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# -----------------------------------------------------------
# AUTH_USER_MODEL — говорим Django использовать нашу модель User
# из приложения api, а не стандартную auth.User
# БЕЗ ЭТОЙ СТРОКИ JWT будет искать пользователей в неправильной таблице!
# -----------------------------------------------------------
AUTH_USER_MODEL = 'api.User'

# -----------------------------------------------------------
# REST_FRAMEWORK — глобальные настройки Django REST Framework.
# Здесь задаём, как API проверяет аутентификацию и права доступа.
# -----------------------------------------------------------
REST_FRAMEWORK = {
    # Метод аутентификации: JWT-токены
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # По умолчанию требуется аутентификация для любого запроса
    # (можно переопределить в конкретном ViewSet)
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Пагинация: возвращать по 20 записей за запрос
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# -----------------------------------------------------------
# SIMPLE_JWT — настройки JWT-токенов.
# ACCESS_TOKEN_LIFETIME  — время жизни токена доступа (30 минут)
# REFRESH_TOKEN_LIFETIME — время жизни токена обновления (7 дней)
# -----------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # False — без blacklist приложения
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',              # Поле ID в нашей модели User
    'USER_ID_CLAIM': 'user_id',         # Как называется в токене
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}


# -----------------------------------------------------------
# CORS — настройки Cross-Origin Resource Sharing.
# Без этого браузер заблокирует запросы от React (порт 3000)
# к Django (порт 8000).
# ⚠️ В продакшене замените CORS_ALLOW_ALL_ORIGINS = False
# и укажите конкретные домены в CORS_ALLOWED_ORIGINS
# -----------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://meticulous-happiness-production-e35d.up.railway.app',
    'http://localhost:3000',
]

# -----------------------------------------------------------
# SECURITY — заголовки безопасности.
# Защищают от XSS, кликджекинга и других атак.
# В режиме разработки некоторые отключены (иначе мешают).
# -----------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# -----------------------------------------------------------
# LOGGING — настройки логирования ошибок и событий.
# Все ошибки пишутся в консоль и файл logs/django.log
# -----------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            # Формат строки лога: время | уровень | модуль | сообщение
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',          # Вывод в консоль
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',  # Файл логов (создайте папку logs/)
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
