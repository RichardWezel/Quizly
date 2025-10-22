from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .utils import create_user, make_access_token_for_user


class JWTAuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

        # Token „fake“ generieren (ohne Login)
        self.access_token = make_access_token_for_user(self.user)

        # Header setzen: Authorization: Bearer <token>
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.list_url = reverse("quiz-list")
        self.create_url = reverse("create-quiz")

    def test_authenticated_get(self):
        """
        Authentifizierter GET-Request mit Bearer-Token.
        Erwartung: 200 OK (oder was deine View zurückgibt).
        """
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_unauthenticated_get(self):
        """
        Authentifizierter GET-Request mit Bearer-Token.
        Erwartung: 200 OK (oder was deine View zurückgibt).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {'INVALIDTOKEN'}")
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED])


