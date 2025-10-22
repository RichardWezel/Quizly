import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")  # .env laden (falls nötig)

import django
django.setup()