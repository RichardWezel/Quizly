from rest_framework import status, generics
from rest_framework.response import Response
from .serializers import CreateQuizSerializer, QuizReadSerializer
from quiz_app.models import Quiz


class CreateQuizView(generics.CreateAPIView):
    serializer_class = CreateQuizSerializer

    def create(self, request, *args, **kwargs):
        # 1) Nur URL validieren
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) Speichern (erzeugt/aktualisiert Quiz + Fragen)
        quiz = serializer.save()

        # 3) Ausgabe
        out = QuizReadSerializer(quiz)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
    
class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizReadSerializer

class QuizDetailView(generics.RetrieveUpdateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizReadSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        try:
            
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            self.perform_update(serializer)
            output_serializer = QuizReadSerializer(
                instance,
                context={**self.get_serializer_context(), 'force_full_details': True}
            )
            return Response(output_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    
