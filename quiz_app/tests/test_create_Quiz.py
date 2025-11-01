import pytest
from django.urls import reverse
from quiz_app.tests.data_factories import make_youtube_url
from rest_framework import status
from quiz_app.models import Quiz, Question


@pytest.mark.django_db
def test_create_quiz_success(api_client, fake_quiz_payload):
    url = reverse("create-quiz")
    payload = {"url": make_youtube_url()}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    # kommt wirklich das zurück, was unser Mock „generiert“ hat?
    assert response.data["title"] == fake_quiz_payload["title"]
    assert len(response.data["questions"]) == 10

    # und ist es wirklich in der DB?
    assert Quiz.objects.count() == 1
    quiz = Quiz.objects.first()
    assert quiz.title == fake_quiz_payload["title"]
    assert quiz.video_url == payload["url"]

    # Fragen sollten auch in DB sein
    assert Question.objects.filter(quiz=quiz).count() == 10


@pytest.mark.django_db
def test_create_quiz_rejects_invalid_youtube_url(api_client):
    url = reverse("create-quiz")
    payload = {"url": "https://example.com/not-youtube"}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # kommt deine Fehlermeldung aus validate_url?
    assert "url" in response.data
    assert "YouTube" in str(response.data["url"][0]) or "Ungültige" in str(response.data["url"][0])


@pytest.mark.django_db
def test_create_quiz_fails_when_llm_returns_less_than_10_questions(api_client, monkeypatch):
    """
    Wir wollen auch testen, dass DEINE strikte Validierung greift.
    Also mocken wir hier bewusst „kaputtes“ LLM-JSON.
    """
    from quiz_app.api.serializers import CreateQuizSerializer

    def fake_generate(self, url):
        return {
            "title": "too few",
            "description": "x",
            "questions": [
                {
                    "question_title": "only one",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
            ],
        }

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

    url = reverse("create-quiz")
    payload = {"url": "https://www.youtube.com/watch?v=abc"}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "muss genau 10 Fragen enthalten" in str(response.data["questions"][0])
