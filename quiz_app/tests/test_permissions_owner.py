import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from quiz_app.models import Quiz
from quiz_app.api.permissions import IsOwnerOrReadOnly  # Beispiel

User = get_user_model()

@pytest.mark.django_db
def test_is_owner_or_read_only_allows_safe_methods():
    perm = IsOwnerOrReadOnly()
    req = APIRequestFactory().get("/api/quizzes/")
    obj_owner = User.objects.create_user(username="u1")
    quiz = Quiz.objects.create(title="t", description="", owner=obj_owner)
    assert perm.has_object_permission(req, None, quiz) is True

@pytest.mark.django_db
def test_is_owner_or_read_only_denies_non_owner_write():
    perm = IsOwnerOrReadOnly()
    req = APIRequestFactory().put("/api/quizzes/1/", {"title": "x"})
    req.user = User.objects.create_user(username="intruder")
    owner = User.objects.create_user(username="owner")
    quiz = Quiz.objects.create(title="t", description="", owner=owner)
    assert perm.has_object_permission(req, None, quiz) is False

@pytest.mark.django_db
def test_is_owner_or_read_only_allows_owner_write():
    perm = IsOwnerOrReadOnly()
    owner = User.objects.create_user(username="owner")
    req = APIRequestFactory().patch("/api/quizzes/1/", {"title": "x"})
    req.user = owner
    quiz = Quiz.objects.create(title="t", description="", owner=owner)
    assert perm.has_object_permission(req, None, quiz) is True
