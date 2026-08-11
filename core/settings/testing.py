# core/settings/testing.py

from .base import *

DEBUG = False

# Base de données en mémoire pour les tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Pas de Celery en mode test
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Pas de cache externe
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Désactiver Cloudinary en test — stockage local
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "test_media"

# Pas de CORS en test
CORS_ALLOW_ALL_ORIGINS = True

# Email en mémoire
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Pas de password validators en test pour accélérer
AUTH_PASSWORD_VALIDATORS = []
