# core/settings/__init__.py
# Permet l'import direct du package core.settings en chargeant la configuration appropriée.

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    base_dir = Path(__file__).resolve().parent.parent.parent
    load_dotenv(base_dir / ".env")
except ImportError:
    pass

env_mode = os.getenv("DJANGO_ENV", "development").lower()

if env_mode == "production":
    from .production import *
elif env_mode == "testing":
    from .testing import *
else:
    from .development import *
