from rest_framework import serializers
from quiz_app.models import Quiz, Question
import yt_dlp
import os

def yt_url_to_id(url):
    """Extract the YouTube video ID from a URL."""
    # Example URL: https://www.youtube.com/watch?v=VIDEO_ID
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return None

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
        # Erzeugten Dateipfad bestimmen
        filename = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(filename)[0] + ".mp3"
        return mp3_path

class CreateQuizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'questions']

    def create(self, validated_data):
        # Implement quiz creation logic here
        pass



