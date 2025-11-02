from rest_framework import serializers
from quiz_app.models import Quiz, Question
from rest_framework import serializers
from quiz_app.models import Quiz, Question
from quiz_app.api.utils import validate_youtube_url, download_audio, transcript_audio
import json
from google import genai
from django.db import transaction

class QuestionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer']

class QuizReadSerializer(serializers.ModelSerializer):
    questions = QuestionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']

def _download_and_transcripe_yt_video(url):
    # Validierung der YouTube-URL
        try: # pragma: no cover
            mp3_path = download_audio(url)
            text = transcript_audio(mp3_path)
            print("-> Text transcription successful.")
            return text
        except Exception:
            raise serializers.ValidationError("Error processing the YouTube video (download/transcript).")



class CreateQuizSerializer(serializers.Serializer):
    print("-> Initializing CreateQuizSerializer...")
    url = serializers.URLField()

    # ---------- Validierung ----------
    def validate_url(self, url):
        if not validate_youtube_url(url):
            raise serializers.ValidationError("Ungültige YouTube-URL.")
        return url
    
    def _build_quiz_prompt(self, transcription: str) -> str:
        promt=( # pragma: no cover
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
        return promt # pragma: no cover
    
    # ---------- Quiz-Generierung ----------
    def _generate_quiz_from_transcript(self, url):
        transcription = _download_and_transcripe_yt_video(url)

        print("-> Generating quiz from transcript...")

        client = genai.Client()
        prompt = self._build_quiz_prompt(transcription)
        response_gemini = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
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
        except json.JSONDecodeError:
            print("-> Failed to parse generated content as JSON.")
            raise ValueError("Generated content is not valid JSON")
        
        return quiz_json
    
        
    def create(self, validated_data):
        print("-> Creating or updating quiz in the database...")
        url = validated_data['url']
        user = self.context['request'].user  # <--- Owner

        # 1) Generiere Quiz-Daten
        quiz_json = self._generate_quiz_from_transcript(url)

        # 2) Minimale Struktur-Validierung
        title = quiz_json.get("title")
        description = quiz_json.get("description", "")
        questions = quiz_json.get("questions")

        if not isinstance(title, str) or not title.strip():
            raise serializers.ValidationError(
                {"title": "Fehlender oder leerer Titel im generierten Quiz."}
        )
        if not isinstance(questions, list) or len(questions) != 10:
           raise serializers.ValidationError(
            {"questions": ["Das generierte Quiz muss genau 10 Fragen enthalten."]}
        )


        # 3) DB-Transaktion (idempotent pro video_url)
        with transaction.atomic():
            # Upsert per video_url: vorhandenes Quiz aktualisieren & Fragen ersetzen
            quiz, created = Quiz.objects.get_or_create(
                video_url=url,
                defaults={
                    "title": title.strip(), 
                    "description": description.strip(),
                    "owner": user
                }
            )
            if not created:
                changed_fields = ["title", "description", "updated_at"]
                quiz.title = title.strip()
                quiz.description = description.strip()
                if quiz.owner_id is None:
                    quiz.owner = user
                    changed_fields.append("owner")
                quiz.save(update_fields=changed_fields)

                quiz.questions.all().delete()

            # Fragen validieren & anlegen (bulk)
            question_objs = []
            for idx, q in enumerate(questions, start=1):
                q_title = q.get("question_title")
                opts = q.get("question_options")
                ans = q.get("answer")

                if not isinstance(q_title, str) or not q_title.strip():
                    raise serializers.ValidationError(f"Frage {idx}: 'question_title' fehlt oder ist leer.")
                if not isinstance(opts, list) or len(opts) != 4:
                    raise serializers.ValidationError(f"Frage {idx}: 'question_options' muss eine Liste mit exakt 4 Einträgen sein.")
                # Duplikate entfernen wir nicht automatisch – lieber strikt validieren:
                if len(set(opts)) != 4:
                    raise serializers.ValidationError(f"Frage {idx}: 'question_options' enthält Duplikate.")
                if ans not in opts:
                    raise serializers.ValidationError(f"Frage {idx}: 'answer' muss eine der Optionen sein.")

                question_objs.append(Question(
                    quiz=quiz,
                    question_title=q_title.strip(),
                    question_options=opts,
                    answer=ans.strip()
                ))

            Question.objects.bulk_create(question_objs)
            print("-> Quiz creation/update completed.")
        return quiz   
        
        