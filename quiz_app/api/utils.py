import os
import re
import yt_dlp
import whisper

def validate_youtube_url(url):
    """Validate if the provided URL is a valid YouTube URL."""
    print(f"-> Validating YouTube URL: {url}")
    valid_prefixes = (
        "https://www.youtube.com/watch?v=",
        "http://www.youtube.com/watch?v=",
        "https://youtu.be/",
        "http://youtu.be/"
    )
    return isinstance(url, str) and url.startswith(valid_prefixes)

def yt_url_to_id(url: str):
    """Extract the YouTube video ID from a URL."""
    if not isinstance(url, str):
        return None  # schützt vor z. B. None oder Integer-Eingaben

    # Standard-YouTube-Link (mit ?v=)
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]

    # Kurzlink youtu.be/<video_id>
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else None

def _sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    return re.sub(r'[\\/*?:"<>|]+', "_", name).strip()

def download_audio(url):
    """Download audio from a YouTube URL and save it as an MP3 file."""
    print(f"-> Downloading audio from: {url}")

    output_dir = os.path.join("quiz_app", "audio_file")
    os.makedirs(output_dir, exist_ok=True)
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
        filename = ydl.prepare_filename(info)         
        mp3_path = os.path.splitext(filename)[0] + ".mp3"

        base = _sanitize_filename(os.path.splitext(os.path.basename(mp3_path))[0])
        safe_mp3 = os.path.join(output_dir, base + ".mp3")
        if mp3_path != safe_mp3 and os.path.exists(mp3_path):
            os.replace(mp3_path, safe_mp3)

        return safe_mp3 if os.path.exists(safe_mp3) else mp3_path
    
def transcript_audio(mp3_path: str):
    """
    Transcribes audio using Whisper, saves a .txt file in quiz_app/text_file/,
    and returns (text, text_file_path).
    """
    print(f"-> Transcribing audio file: {mp3_path}")
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"Audio file not found: {mp3_path}")

    model = whisper.load_model("base")
    result = model.transcribe(mp3_path, fp16=False)
    text = (result.get("text") or "").strip()

    if not text:
        raise ValueError("No transcribed text found")
    else:
        os.remove(mp3_path)
        print(f"-> Deleted audiofile at: {mp3_path}")
    return text