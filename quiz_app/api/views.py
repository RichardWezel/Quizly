# views.py (Ausschnitt)
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import CreateQuizSerializer, QuizReadSerializer

class CreateQuizView(generics.GenericAPIView):
    
    serializer_class = CreateQuizSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return Response(QuizReadSerializer(quiz).data, status=status.HTTP_201_CREATED)
