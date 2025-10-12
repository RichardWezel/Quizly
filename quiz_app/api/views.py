# views.py (Ausschnitt)
from rest_framework import status, generics
from rest_framework.response import Response
from .serializers import CreateQuizSerializer, QuizReadSerializer
from quiz_app.models import Quiz


class CreateQuizView(generics.GenericAPIView):
    
    serializer_class = CreateQuizSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return Response(QuizReadSerializer(quiz).data, status=status.HTTP_201_CREATED)

class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizReadSerializer
