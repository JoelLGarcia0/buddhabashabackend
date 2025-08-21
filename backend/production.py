"""
Production settings for Buddha Basha
"""
from .settings import *

# Production security settings
DEBUG = False

# SECRET_KEY - critical for Django to function
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    print("CRITICAL ERROR: DJANGO_SECRET_KEY not set in production!")
    print("Please set this environment variable on your deployment platform")
    # Generate a temporary key (this should be replaced with a real one)
    import secrets
    SECRET_KEY = secrets.token_urlsafe(50)
    print(f"Generated temporary SECRET_KEY: {SECRET_KEY[:20]}...")

# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ALLOWED_HOSTS - critical for Django to accept requests
allowed_hosts = os.getenv("ALLOWED_HOSTS")
if not allowed_hosts:
    print("CRITICAL ERROR: ALLOWED_HOSTS not set in production!")
    print("Please set this environment variable on your deployment platform")
    # Set a default that should work for most deployments
    ALLOWED_HOSTS = ["*"]  # WARNING: This allows all hosts - set properly in production
    print("Set ALLOWED_HOSTS to ['*'] as fallback - PLEASE FIX THIS!")
else:
    ALLOWED_HOSTS = allowed_hosts.split(",")

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://www.buddhabashajewelry.com",
    "https://buddhabashafrontend.vercel.app",
]

# Database connection pooling (if using PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PWD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Static files - simplified since no static files exist
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Create empty staticfiles directory if it doesn't exist
if not os.path.exists(STATIC_ROOT):
    try:
        os.makedirs(STATIC_ROOT, exist_ok=True)
        print(f"Created staticfiles directory: {STATIC_ROOT}")
    except Exception as e:
        print(f"Warning: Could not create staticfiles directory: {e}")

# Use basic WhiteNoise storage since no static files to compress
STATICFILES_STORAGE = 'whitenoise.storage.WhiteNoiseStaticFilesStorage'

# Disable static file serving since no files exist
WHITENOISE_USE_FINDERS = False

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Remove the whitenoise middleware insertion since it's now in base settings
# WhiteNoise is already configured in the base settings.py
