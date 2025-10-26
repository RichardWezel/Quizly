# conftest.py
import os
import warnings
from pathlib import Path

# 🔇 Warnung kategoriebasiert unterdrücken (greift immer)
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Django-Setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# .env laden (falls vorhanden)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

import django
django.setup()
