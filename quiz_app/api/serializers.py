from rest_framework import serializers
from quiz_app.models import Quiz
from utils import validate_youtube_url


class CreateQuizSerializer(serializers.ModelSerializer):
    url = serializers.URLField(required=True)

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'questions']

    if not validate_youtube_url(url):
        raise ValueError("Invalid YouTube URL")

    def create(self, validated_data):
        # Implement quiz creation logic here
        pass



# serializers.py
# from rest_framework import serializers
# from .models import Quiz, Question

# class QuestionReadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Question
#         fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

# class QuizReadSerializer(serializers.ModelSerializer):
#     questions = QuestionReadSerializer(many=True, read_only=True)

#     class Meta:
#         model = Quiz
#         fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']

# class CreateQuizSerializer(serializers.Serializer):
#     url = serializers.URLField()

#     def create(self, validated_data):
#         url = validated_data['url']
#         # hier: YouTube transkribieren/parsen -> Fragen erzeugen
#         quiz = Quiz.objects.create(
#             title="Quiz Title",               # dynamisch befüllen
#             description="Quiz Description",   # dynamisch befüllen
#             video_url=url
#         )
#         # Beispiel-Frage (später dynamisch)
#         Question.objects.create(
#             quiz=quiz,
#             question_title="Question 1",
#             question_options=["Option A", "Option B", "Option C", "Option D"],
#             answer="Option A"
#         )
#         return quiz
