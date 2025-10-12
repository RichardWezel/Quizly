from rest_framework import serializers
from quiz_app.models import Quiz, Question
from rest_framework import serializers
from quiz_app.models import Quiz, Question
from quiz_app.api.utils import validate_youtube_url, download_audio, transcript_audio
import json
from google import genai

class QuestionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer']

class QuizReadSerializer(serializers.ModelSerializer):
    questions = QuestionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']

def download_and_transcripe_yt_video(url):
    # Validierung der YouTube-URL
    
        
        try:
            mp3_path = download_audio(url)
            text = transcript_audio(mp3_path)
            print("-> Text transcription successful.")
            return text
        except Exception:
            raise ValueError("Error processing the YouTube video. Not able to download or transcribe.")

class CreateQuizSerializer(serializers.Serializer):
    url = serializers.URLField()

    def create(self, validated_data):
        url = validated_data['url']

        # Validierung der YouTube-URL
        if not validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL")
        
        # download and transcripe YouTube-Video
        transcription =  download_and_transcripe_yt_video(url)

        # Generierung von Fragen 
        print("-> Generating quiz from transcript...")
        client = genai.Client()
        response_gemini = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
            "Based on the following transcript, generate a quiz in valid JSON format.\n\n"
            f"Transcript:\n{transcription}\n\n"
            "The quiz must follow this exact structure:\n\n"
            "{\n"
            '  "title": "Create a concise quiz title based on the topic of the transcript.",\n'
            '  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",\n'
            '  "questions": [\n'
            "    {\n"
            '      "question_title": "The question goes here.",\n'
            '      "question_options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "answer": "The correct answer from the above options"\n'
            "    },\n"
            "    ...\n"
            "    (exactly 10 questions)\n"
            "  ]\n"
            "}\n\n"
            "Requirements:\n"
            "- Each question must have exactly 4 distinct answer options.\n"
            "- Only one correct answer is allowed per question, and it must be present in 'question_options'.\n"
            "- The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).\n"
            "- Do not include explanations, comments, or any text outside the JSON."
            ),
            config={
            "response_mime_type": "application/json",
            },
        )

        quiz_data = response_gemini
        if hasattr(quiz_data, 'text'):
            quiz_data = quiz_data.text
        elif hasattr(quiz_data, 'content'):
            quiz_data = quiz_data.content
        
        try:
            quiz_json = json.loads(quiz_data)
            print("-> Quiz generation successful.")
            return quiz_json
        except json.JSONDecodeError:
            raise ValueError("Generated content is not valid JSON")
        