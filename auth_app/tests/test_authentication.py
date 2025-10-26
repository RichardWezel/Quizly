from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from uuid import uuid4

from .utils import create_user, make_access_token_for_user

def unique_user_data():
    """Erzeugt garantiert eindeutige Daten für eine Neuregistrierung."""
    uid = uuid4().hex[:8]
    return {
        "username": f"user_{uid}",
        "email": f"{uid}@example.com",
        "password": "pass1234",
        "confirmed_password": "pass1234",
    }

class JWTAuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = create_user() # alice, alice@example.com, pass1234
        self.access_token = make_access_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.register_url = reverse("registration")
        self.login_url = reverse("token_obtain_pair")
        self.logout_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")

        self.new_user_ok = unique_user_data()
        bad = unique_user_data()
        bad["confirmed_password"] = "wrong"
        self.new_user_bad = bad

    def test_successful_registration(self):

        self.client.credentials()  # Header leeren
        response = self.client.post(self.register_url, data=self.new_user_ok, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_unsuccessful_registration(self):
        self.client.credentials()
        response = self.client.post(self.register_url, data=self.new_user_bad, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

