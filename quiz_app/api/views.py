from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import CreateQuizSerializer, QuizReadSerializer
from quiz_app.models import Quiz
from .permissions import IsOwnerOrReadOnly
from auth_app.api.authentication import CookieJWTAuthentication


@method_decorator(csrf_exempt, name="dispatch")
class CreateQuizView(generics.CreateAPIView):
    '''API view to create a Quiz from a YouTube URL.'''
    serializer_class = CreateQuizSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quiz = serializer.save()

        out = QuizReadSerializer(quiz)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
    
class QuizListView(generics.ListAPIView):
    '''API view to list all Quizzes.'''
    queryset = Quiz.objects.all()
    serializer_class = QuizReadSerializer
    permission_classes = [IsAuthenticated]


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''API view to retrieve, update, or delete a Quiz by ID.'''
    queryset = Quiz.objects.all()
    serializer_class = QuizReadSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'


    def update(self, request, *args, **kwargs):
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

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied:
            raise
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
