import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from auth_app.tests.utils import create_user, make_access_token_for_user


@pytest.fixture
def user(db):
    return create_user(username="testuser", password="secret")


@pytest.fixture
def api_client(user):
    client = APIClient()
    access_token = make_access_token_for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return client


@pytest.fixture
def fake_quiz_payload():
    # DAS ist das, was sonst Gemini zurückgeben würde
    return {
        "title": "Claude Skills: Building AI Systems for Exponential Growth",
        "description": "Discover how Claude Skills transform AI usage...",
        "questions": [
            {
                "question_title": "What problem does the speaker identify ...?",
                "question_options": [
                    "They don't know how to write effective prompts.",
                    "They primarily use AI as a tool for prompts, not for building scalable systems.",
                    "They struggle with the complex setup of AI tools.",
                    "They only use AI for personal tasks, not for business."
                ],
                "answer": "They primarily use AI as a tool for prompts, not for building scalable systems."
            },
        ] + [
            {
                "question_title": f"Dummy question {i}",
                "question_options": ["A", "B", "C", "D"],
                "answer": "A",
            }
            for i in range(2, 11) 
        ]
    }


@pytest.fixture(autouse=True)
def mock_quiz_generation(monkeypatch, fake_quiz_payload):
    """
    Dieser Fixture läuft AUTOMATISCH für alle Tests in diesem Ordner.
    Er sorgt dafür, dass der Serializer NIE wirklich YouTube/Gemini aufruft.
    """

    from quiz_app.api import serializers as quiz_serializers

    # wir ersetzen die Methode direkt an der Klasse!
    def fake_generate(self, url):
        return fake_quiz_payload

    monkeypatch.setattr(
        quiz_serializers.CreateQuizSerializer,
        "_generate_quiz_from_transcript",
        fake_generate,
    )
