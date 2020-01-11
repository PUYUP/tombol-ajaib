from .base import *
from .project import *

DEBUG = False
ALLOWED_HOSTS = ['localhost', '::1', '127.0.0.1', 'tombol-ajaib.herokuapp.com']

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework_simplejwt.authentication.JWTAuthentication'
]


# Django Sessions
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_HTTPONLY = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = 'DENY'


# Django csrf
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/csrf/
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = []


# Django CORS
# ------------------------------------------------------------------------------
# https://pypi.org/project/django-cors-headers/
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = []


# Static files (CSS, JavaScript, Images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# Add configuration for static files storage using whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'd4lib9ig86685r',
        'USER': 'omydmxfxqmhhtr',
        'PASSWORD': '44f403ca1021ab69881bb0cb9f711326a3809fe3b4d848879d79783498dfb977',
        'HOST': 'ec2-54-235-89-123.compute-1.amazonaws.com',
        'PORT': '5432'
    }
}
