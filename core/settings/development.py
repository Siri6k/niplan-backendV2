# core/settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# CORS ouvert en développement
CORS_ALLOW_ALL_ORIGINS = True

# Email dans la console — pas besoin de SMTP local
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# SQLite par défaut si DATABASE_URL n'est pas défini
# (déjà géré dans base.py avec le fallback sqlite)

# Logging verbeux
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
