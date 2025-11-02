import pytest
from django.urls import reverse

from rest_framework import status
from rest_framework.exceptions import ValidationError

from quiz_app.models import Quiz, Question
from quiz_app.api.serializers import CreateQuizSerializer


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

# -------------------------------
# 1) Direkter Serializer-Test
# -------------------------------
@pytest.mark.django_db
def test_create_quiz_creates_quiz_and_questions(monkeypatch, django_user_model, rf):
    VALID_YT = "https://www.youtube.com/watch?v=abc123"
    # 1) User anlegen
    user = django_user_model.objects.create_user(username="richard", password="123456")

    # 2) Serializer-Kontext mit Request
    request = rf.post("/api/quizzes/", {"url": VALID_YT})
    request.user = user

    # 3) LLM-Funktion mocken
    def fake_generate(self, url):
        return make_valid_quiz_json()

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

    # 4) Serializer instanzieren
    serializer = CreateQuizSerializer(
        data={"url": VALID_YT},
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors

    quiz = serializer.save()

    # 5) Prüfen
    assert Quiz.objects.count() == 1
    assert Question.objects.count() == 10
    assert quiz.title == "Python Grundlagen"
    assert quiz.owner == user
    assert quiz.video_url == VALID_YT


@pytest.mark.django_db
def test_create_quiz_updates_existing_quiz(monkeypatch, django_user_model, rf):
    VALID_YT = "https://www.youtube.com/watch?v=abc123"
    user = django_user_model.objects.create_user(username="richard", password="123456")

    request = rf.post("/api/quizzes/", {"url": VALID_YT})
    request.user = user

    # erstes Quiz: Titel 1
    def fake_generate_first(self, url):
        data = make_valid_quiz_json()
        data["title"] = "Titel 1"
        return data

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate_first)

    serializer = CreateQuizSerializer(
        data={"url": VALID_YT},
        context={"request": request},
    )
    assert serializer.is_valid()
    quiz = serializer.save()
    assert quiz.title == "Titel 1"
    assert Question.objects.count() == 10

    # zweiter Durchlauf: jetzt neuer Titel
    def fake_generate_second(self, url):
        data = make_valid_quiz_json()
        data["title"] = "Neuer Titel"
        return data

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate_second)

    serializer2 = CreateQuizSerializer(
        data={"url": VALID_YT},
        context={"request": request},
    )
    assert serializer2.is_valid()
    quiz2 = serializer2.save()

    # Prüfen: immer noch nur 1 Quiz, aber Fragen neu
    assert Quiz.objects.count() == 1
    assert Question.objects.count() == 10
    assert quiz2.title == "Neuer Titel"


@pytest.mark.django_db
def test_create_quiz_fails_when_answer_not_in_options(monkeypatch, django_user_model, rf):
    VALID_YT = "https://www.youtube.com/watch?v=abc123"
    user = django_user_model.objects.create_user(username="richard", password="123456")
    request = rf.post("/api/quizzes/", {"url": VALID_YT})
    request.user = user

    def fake_generate(self, url):
        data = make_valid_quiz_json()
        data["questions"][0]["answer"] = "Z"  # nicht in ["A","B","C","D"]
        return data

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

    serializer = CreateQuizSerializer(
        data={"url": VALID_YT},
        context={"request": request},
    )
    assert serializer.is_valid()

    with pytest.raises(ValidationError) as exc:
        serializer.save()

    assert "muss eine der Optionen sein" in str(exc.value)


# -------------------------------
# 2) API-Tests (mit api_client)
# -------------------------------
@pytest.mark.django_db
def test_create_quiz_rejects_invalid_youtube_url(api_client):
    url = reverse("create-quiz")
    payload = {"url": "https://example.com/not-youtube"}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "url" in response.data
    # kommt deine Fehlermeldung aus validate_url?
    assert "YouTube" in str(response.data["url"][0]) or "Ungültige" in str(response.data["url"][0])


@pytest.mark.django_db
def test_create_quiz_fails_when_llm_returns_less_than_10_questions(api_client, monkeypatch):
    """
    Wir wollen auch testen, dass DEINE strikte Validierung greift.
    Also mocken wir hier bewusst „kaputtes“ LLM-JSON.
    """
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
    assert "questions" in response.data
    assert "muss genau 10 Fragen enthalten" in str(response.data["questions"][0])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fake_payload",
    [
        {"title": ""},          # leerer Titel
        {"description": "ok"},  # fehlender Titel
    ],
)
def test_create_quiz_rejects_missing_or_empty_title(api_client, monkeypatch, fake_payload):
    def fake_generate(self, url):
        questions = [
            {
                "question_title": f"q{i}",
                "question_options": ["A", "B", "C", "D"],
                "answer": "A",
            }
            for i in range(10)
        ]
        result = dict(fake_payload)
        result.setdefault("description", "x")
        result["questions"] = questions
        return result

    monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

    url = reverse("create-quiz")
    payload = {"url": "https://www.youtube.com/watch?v=abc"}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "title" in response.data
    @pytest.mark.django_db
    def test_create_quiz_sets_owner_when_none(monkeypatch, django_user_model, rf):
        VALID_YT = "https://www.youtube.com/watch?v=abc123"
        user = django_user_model.objects.create_user(username="richard", password="123456")
        other_user = django_user_model.objects.create_user(username="other", password="123456")

        request = rf.post("/api/quizzes/", {"url": VALID_YT})
        request.user = user

        # Quiz ohne Owner erstellen
        quiz = Quiz.objects.create(
            title="Test Quiz",
            description="Test Description",
            video_url=VALID_YT,
            owner=None
        )

        def fake_generate(self, url):
            return {
                "title": quiz.title,
                "description": quiz.description,
                "questions": [
                    {
                        "question_title": f"Frage {i}",
                        "question_options": ["A", "B", "C", "D"],
                        "answer": "A",
                    }
                    for i in range(1, 11)
                ],
            }

        monkeypatch.setattr(CreateQuizSerializer, "_generate_quiz_from_transcript", fake_generate)

        serializer = CreateQuizSerializer(
            data={"url": VALID_YT},
            context={"request": request},
        )
        assert serializer.is_valid()
        updated_quiz = serializer.save()

        # Prüfen ob Owner gesetzt wurde
        assert updated_quiz.owner == user
        assert Quiz.objects.count() == 1
