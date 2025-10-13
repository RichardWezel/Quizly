from django.urls import path
from quiz_app.api.views import CreateQuizView, QuizListView, QuizDetailView

urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='create-quiz'),
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/<int:id>/', QuizDetailView.as_view(), name='quiz-detail'),
]