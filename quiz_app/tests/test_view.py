import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from quiz_app.models import Quiz
from quiz_app.api.serializers import CreateQuizSerializer


# -------------------------------------------------------------------
# Hilfsdaten für das Fake-LLM
# -------------------------------------------------------------------
def make_valid_quiz_json():
    return {
        "title": "Python Grundlagen",
        "description": "Ein Quiz zu Python Basics",
        "questions": [
            {
                "question_title": f"Frage {i}",
                "question_options": ["A", "B", "C", "D"],
                "answer": "A",
            }
            for i in range(1, 11)
        ],
    }


# ============================================================
# A) CreateQuizView testen
# ============================================================
@pytest.mark.django_db
def test_create_quiz_view_creates_quiz(monkeypatch):
    client = APIClient()

    # 1) User anlegen und einloggen
    user = User.objects.create_user(username="richard", password="123456")
    client.force_authenticate(user=user)

    # 2) LLM-Funktion im Serializer mocken
    def fake_generate(self, url):
        return make_valid_quiz_json()

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

    # 3) Request abschicken
    url = reverse("create-quiz")  # muss zu deiner urls.py passen
    payload = {"url": "https://www.youtube.com/watch?v=abc123"}

    response = client.post(url, data=payload, format="json")

    # 4) Prüfen
    assert response.status_code == status.HTTP_201_CREATED
    assert Quiz.objects.count() == 1

    quiz = Quiz.objects.first()
    assert quiz.title == "Python Grundlagen"
    assert quiz.owner == user

    # Response sollte die Daten aus dem Read-Serializer enthalten
    assert response.data["title"] == "Python Grundlagen"


@pytest.mark.django_db
def test_create_quiz_view_requires_auth(monkeypatch):
    client = APIClient()

    # trotzdem LLM mocken, damit er nicht ins Netz will
    monkeypatch.setattr(
        CreateQuizSerializer,
        "_generate_quiz_from_transcript",
        lambda self, url: make_valid_quiz_json(),
    )

    url = reverse("create-quiz")
    payload = {"url": "https://www.youtube.com/watch?v=abc123"}

    response = client.post(url, data=payload, format="json")

    # nicht eingeloggt → 401
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ============================================================
# B) QuizDetailView testen
# ============================================================
@pytest.mark.django_db
class TestQuizDetailView:
    def setup_method(self):
        self.client = APIClient()
        # 1) Owner anlegen
        self.user = User.objects.create_user(username="owner", password="123456")
        # 2) Quiz anlegen, das diesem Owner gehört
        self.quiz = Quiz.objects.create(
            title="Altes Quiz",
            description="desc",
            video_url="https://www.youtube.com/watch?v=abc123",
            owner=self.user,
        )

    def test_update_quiz_authenticated_owner(self):
        # Owner einloggen
        self.client.force_authenticate(user=self.user)

        url = reverse("quiz-detail", kwargs={"id": self.quiz.id})

        data = {
            "title": "Updated Quiz Title",
            "description": "neue beschreibung",
        }

        response = self.client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # aus DB neu laden
        self.quiz.refresh_from_db()
        assert self.quiz.title == "Updated Quiz Title"

    def test_update_quiz_unauthenticated_user(self):
        url = reverse("quiz-detail", kwargs={"id": self.quiz.id})
        data = {"title": "Updated Quiz Title"}

        response = self.client.patch(url, data, format="json")

        # nicht eingeloggt → 401/403 (je nach Einstellungen)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_update_quiz_not_owner(self):
        # anderer User
        another_user = User.objects.create_user(username="another", password="testpass")
        self.client.force_authenticate(user=another_user)

        url = reverse("quiz-detail", kwargs={"id": self.quiz.id})
        data = {"title": "Updated Quiz Title"}

        response = self.client.patch(url, data, format="json")

        # wegen IsOwnerOrReadOnly → 403
        assert response.status_code == status.HTTP_403_FORBIDDEN
