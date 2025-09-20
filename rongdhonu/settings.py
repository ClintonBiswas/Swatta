from celery.schedules import crontab
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'user',
    'product',
    'blog',
    'pool',
    'crispy_forms',
    'crispy_bootstrap5',
    'compressor',
    'django.contrib.sites',
]
SITE_ID = 3

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTH_USER_MODEL = 'user.CustomUser'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 90  # 90 days
SESSION_SAVE_EVERY_REQUEST = True

# SMS
BULKSMS_API_URL = "http://bulksmsbd.net/api/smsapi"
BULKSMS_API_KEY = config("BULKSMS_API_KEY")
BULKSMS_SENDER_ID = config("BULKSMS_SENDER_ID")

SITE_DOMAIN = config("SITE_DOMAIN", default="http://127.0.0.1:8000/")

REDIS_URL = config("REDIS_URL", default='redis://localhost:6379')

# Celery Configuration
CELERY_BROKER_URL = f'{REDIS_URL}/0'  # Database 0 for Celery
CELERY_RESULT_BACKEND = f'{REDIS_URL}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",  
        "LOCATION": f'{REDIS_URL}/1', 
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            
            "SOCKET_CONNECT_TIMEOUT": 5, 
            "SOCKET_TIMEOUT": 5,         
            "IGNORE_EXCEPTIONS": True,    
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rongdhonu.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'user.context_processors.global_subcategories',
                'user.context_processors.facebook_pixel',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rongdhonu.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': config("DB_HOST"),
        'PORT': config("DB_PORT"),
    },
    # 'pgadmin': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'letshop_pgadmin',
    #     'USER': 'pgadmin_user',
    #     'PASSWORD': 'SecurePass123!',
    #     'HOST': '192.168.144.1',
    #     'PORT': '5432',
    # }
}
# I don't want to change database settings. if needed i will do it later.



# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f'Swatta - সত্তা <{EMAIL_HOST_USER}>'

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

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  
STATIC_ROOT = BASE_DIR / "staticfiles"
# Define STATICFILES_FINDERS first
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # Then add compressor finder
]
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_ROOT = STATIC_ROOT
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


LOGIN_URL = '/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#Facebook pixel settings
FACEBOOK_PIXEL_ID = config("FACEBOOK_PIXEL_ID")
FACEBOOK_ACCESS_TOKEN = config("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_API_VERSION = config("FACEBOOK_API_VERSION")

