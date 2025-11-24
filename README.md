# Quizly — Backend

![Quizly Logo](/assets/logoheader.png)

Eine Django-basierte REST-API für die Quiz-Applikation "Quizly". Dieses Backend bietet Authentifizierung, Quiz-Erstellung (z. B. aus YouTube-Audios), Quiz-Verwaltung und Testabdeckung mittels pytest.

## Inhalt dieser README
- Kurzbeschreibung
- Voraussetzungen
- Installation & Entwicklung (lokal)
- Tests
- Projektstruktur (Kurzüberblick)
- Hinweise zur Konfiguration

## Kurzbeschreibung

Das Backend stellt Endpunkte zur Verfügung, mit denen Nutzer Quizzes erstellen, abrufen, bearbeiten und löschen können. Es gibt eine eigene Authentifizierungs-App (`auth_app`) sowie die Haupt-Quiz-Logik in `quiz_app`. Zusätzlich werden Tools wie Whisper/yt-dlp für Audio-Transkription und externe AI-Services zur Quiz-Generierung verwendet (sofern konfiguriert).

## Voraussetzungen

- Python **3.12 oder höher**
  Hinweis: Das macOS-System-Python (3.9) funktioniert NICHT für dieses Projekt.
  yt-dlp und Whisper nutzen Funktionen, die Python ≥3.10 voraussetzen.
  Siehe Abschnitt "Installation".

- Virtuelle Umgebung (venv)

- ffmpeg (für YouTube-Audio-Extraktion)
  Installation unter macOS:
    brew install ffmpeg

## Installation (lokal)

1. Repo klonen
	```
	git clone https://github.com/RichardWezel/Quizly.git
	cd Quizly
	```

2. Python-Version sicherstellen

Dieses Projekt benötigt Python 3.12 oder höher.
Das macOS-System-Python (z. B. 3.9.6) ist zu alt und führt zu 403-Fehlern bei yt-dlp.

Installation von Python 3.12 über Homebrew:
	```
    brew install python@3.12
	```
Prüfen:
	```
    python3.12 --version
	```

3. Virtuelle Umgebung erstellen und aktivieren
	```
    python3.12 -m venv env
    source env/bin/activate
	```

4. Abhängigkeiten installieren
	```
    pip install --upgrade pip
    pip install -r requirements.txt
	```

Hinweis:
yt-dlp wird automatisch in einer Version installiert, die mit Python 3.12 kompatibel ist.
Die System-Version von yt-dlp (z. B. Homebrew) ist getrennt und nicht relevant.

5. Umgebungsvariablen

	Lege eine `.env`-Datei an!
    Füge dort den Gemini-API-Schlüssel an und den Django SECRET_KEY
	```
    GEMINI_API_KEY="..."
    SECRET_KEY="..."
	```

    API-Schlüssel für Gemini unter https://aistudio.google.com/api-keys?hl=de erstellen.
    Einen eigenen Django Secret-Key erstellen mit 
	```
	python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
	``` 
	im Terminal.

6. Datenbank-Migrationen ausführen
	```
	python manage.py migrate
	```
7. Optional: Superuser anlegen
	```
	python manage.py createsuperuser
	```
8. Server starten
	```
	python manage.py runserver
	```
Die API ist dann standardmäßig unter `http://127.0.0.1:8000/` erreichbar.

## Hinweis zur yt-dlp Version

Die macOS-Version von yt-dlp (z. B. installiert über Homebrew oder als Binary)
kann neuer sein als die PyPI-Version.

Das Backend verwendet ausschließlich die Python-PyPI-Version.
Damit es korrekt läuft, muss die Python-Version >= 3.10 sein
(siehe Voraussetzungen).

## Tests

Das Projekt verwendet `pytest` und `pytest-django`.

1. Tests ausführen
	```
	pytest -q
	```
2. Coverage-Report (falls gewünscht)
	```
	coverage run -m pytest && coverage html
	```
Der Coverage-Report wird im Ordner `htmlcov/` angelegt.

## Wichtige Endpunkte (Beispiele)

- API-Root: `/api/`
- Auth (Registrierung/Login/Token): typischerweise unter `/api/auth/` (siehe `auth_app/api/urls.py`)
- Quiz-Ressourcen: `/api/quizzes/` oder ähnlich (siehe `quiz_app/api/urls.py`)

Hinweis: Die genauen Routen können in `core/urls.py` und den App-`urls.py`-Dateien eingesehen werden.

## Projektstruktur (Kurz)

```
Backend_Quizly/
├── auth_app/        # Authentifizierungs-API, Serializer, Views, Tests
├── quiz_app/        # Logik für Quizzes, API-Views und Tests
├── .env			 # Gemini-API-Key & Django Secret-Key
├── core/            # Projekt-Settings, URLs, WSGI/ASGI
├── assets/          # Static assets (z. B. Logo)
├── manage.py
├── requirements.txt # Zu installierende Apps
└── README.md		 # Anleitung / Handbuch
```

## Entwicklungshinweise
- Nutze die vorhandenen Tests in `auth_app/tests` und `quiz_app/tests` als Referenz für erwartetes Verhalten.
- Wenn du neue Abhängigkeiten hinzufügst, aktualisiere `requirements.txt`.
- Schreibe kleine, isolierte Tests für neue Features und führe `pytest` lokal vor dem Push aus.


Viel Erfolg beim Entwickeln mit Quizly! 🎯

