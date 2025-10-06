import os
import re
import json
import yt_dlp
import whisper

# ---------- Helpers ----------
def validate_youtube_url(url):
    """Validate if the provided URL is a valid YouTube URL."""
    valid_prefixes = (
        "https://www.youtube.com/watch?v=",
        "http://www.youtube.com/watch?v=",
        "https://youtu.be/",
        "http://youtu.be/"
    )
    return isinstance(url, str) and url.startswith(valid_prefixes)

def yt_url_to_id(url: str):
    if not isinstance(url, str):
        return None  # schützt vor z. B. None oder Integer-Eingaben

    # Standard-YouTube-Link (mit ?v=)
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]

    # Kurzlink youtu.be/<video_id>
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else None

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _sanitize_filename(name: str) -> str:
    # einfache Sanitization für Dateinamen
    return re.sub(r'[\\/*?:"<>|]+', "_", name).strip()

# ---------- Download ----------
def download_audio(url):
    """Download audio from a YouTube URL and save it as an MP3 file."""
    # Zielordner definieren (relativ zum Projektverzeichnis)
    output_dir = os.path.join("quiz_app", "audio_file")

    # Falls Ordner noch nicht existiert → erstellen
    os.makedirs(output_dir, exist_ok=True)

    # Pfad-Template für den Dateinamen
    outtmpl_path = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl_path,   
        "postprocessors": [{                   
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",           
            "preferredquality": "192",         
        }],
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)         # original container (z.B. .webm)
        mp3_path = os.path.splitext(filename)[0] + ".mp3"

        # Sicherheitshalber normalisieren
        base = _sanitize_filename(os.path.splitext(os.path.basename(mp3_path))[0])
        safe_mp3 = os.path.join(output_dir, base + ".mp3")
        if mp3_path != safe_mp3 and os.path.exists(mp3_path):
            os.replace(mp3_path, safe_mp3)

        return safe_mp3 if os.path.exists(safe_mp3) else mp3_path
    
# ---------- Transkription ----------
def transcript_audio(file_path: str):
    """
    Transkribiert Audio mit Whisper, speichert .txt in quiz_app/text_file/
    und gibt (text, text_file_path) zurück.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Whisper-Modell laden (base/small/medium/large)
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    text = (result.get("text") or "").strip()

    output_dir = os.path.join("quiz_app", "text_file")
    _ensure_dir(output_dir)

    base_name = _sanitize_filename(os.path.splitext(os.path.basename(file_path))[0])
    text_file_path = os.path.join(output_dir, f"{base_name}.txt")

    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write(text)

    return text, text_file_path


# ---------- End-to-end ----------
def transcribe_audio_of_youtube(url: str, delete_audio: bool = True):
    """
    End-to-end: YouTube-URL -> MP3 downloaden -> transkribieren -> optional MP3 löschen.
    Rückgabe: dict mit { "text", "audio_path", "text_path", "video_id" }
    """
    if not validate_youtube_url(url):
        raise ValueError("Invalid YouTube URL")

    video_id = yt_url_to_id(url)
    if not video_id:
        raise ValueError("Could not extract video ID from URL")

    mp3_path = download_audio(url)
    text, text_path = transcript_audio(mp3_path)

    if delete_audio:
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception:
            pass

    return {
        "text": text,
        "audio_path": mp3_path if not delete_audio else None,
        "text_path": text_path,
        "video_id": video_id,
    }
