from rest_framework import serializers
from quiz_app.models import Quiz


class CreateQuizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'questions']

    def create(self, validated_data):
        # Implement quiz creation logic here
        pass



