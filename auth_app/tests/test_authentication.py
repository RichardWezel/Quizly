from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from uuid import uuid4
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from .utils import create_user, make_access_token_for_user

def unique_user_data():
    """Generates unique user data for registration tests."""
    uid = uuid4().hex[:8]
    return {
        "username": f"user_{uid}",
        "email": f"{uid}@example.com",
        "password": "pass1234",
        "confirmed_password": "pass1234",
    }

class Tests_of_Registration(APITestCase):
    '''Tests for the user registration endpoint.'''
    def setUp(self):
        self.client = APIClient()

        self.user = create_user() # alice, alice@example.com, pass1234
        self.access_token = make_access_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.register_url = reverse("registration")
        
        self.new_user_ok = unique_user_data()
        bad = unique_user_data()
        bad["confirmed_password"] = "wrong"
        self.new_user_bad = bad

    def test_registration_successful(self):

        self.client.credentials()  # Header leeren
        response = self.client.post(self.register_url, data=self.new_user_ok, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_registration_wrong_confirmed_password(self):
        self.client.credentials()
        response = self.client.post(self.register_url, data=self.new_user_bad, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_registration_missing_email(self):
        self.client.credentials()
        data = {
            "username": "newuser",
            "password": "pass1234",
            "confirmed_password": "pass1234",
        }
        response = self.client.post(self.register_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
    
    def test_registration_missing_username(self):
        self.client.credentials()
        data = {
            "email": "richard@gde.de",
            "password": "pass1234",
            "confirmed_password": "pass1234",
        }
        response = self.client.post(self.register_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_invalid_email_format(self):
        """Testet, dass ungültige E-Mail im POST-Body erkannt wird."""
        invalid_data = {
            "username": "testuser",
            "email": "not-an-email",  
            "password": "pass1234",
            "repeat_password": "pass1234"
        }
        self.client.credentials()
        response = self.client.post(self.register_url, data=invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_response_details(self):
        response = self.client.post(self.register_url, data=self.new_user_ok, format="json")

        response_data = {
            "detail": "User created successfully!"
        }
        self.assertEqual(response.data, response_data)

    def test_registration_duplicate_email(self):
        self.client.post(self.register_url, self.new_user_ok, format="json")
        data = unique_user_data()
        data["email"] = self.new_user_ok["email"]
        resp = self.client.post(self.register_url, data, format="json")
        assert resp.status_code == 400
        assert "email" in resp.data

    def test_registration_missing_passwords(self):
        data = {"username": "u1", "email": "u1@example.com"}
        resp = self.client.post(self.register_url, data, format="json")
        assert resp.status_code == 400
        assert "required" in str(resp.data).lower()

    def test_registration_password_hashed(self):
        resp = self.client.post(self.register_url, self.new_user_ok, format="json")
        assert resp.status_code == 201
        from django.contrib.auth import get_user_model
        U = get_user_model()
        u = U.objects.get(username=self.new_user_ok["username"])
        assert u.password != self.new_user_ok["password"]
        assert u.check_password(self.new_user_ok["password"])


class Tests_of_Login(APITestCase):
    '''Tests for the user login endpoint.'''
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.username = "alice_login"
        self.email = "alice_login@example.com"
        self.password = "pass1234"
        
        User.objects.create_user(username=self.username, email=self.email, password=self.password)

        self.expected_samesite = "Lax"
        self.expected_secure = True
        self.expected_httponly = True


    def test_login_successful(self):
        resp = self.client.post(self.login_url, data={"username": self.username, "password": self.password}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        
    def test_login_wrong_password(self):
        resp = self.client.post(self.login_url, data={"username": self.username, "password": "wrongpass"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.data)

    def test_login_response(self):
        resp = self.client.post(self.login_url, data={"username": self.username, "password": self.password}, format="json")
        response_data = {
            "detail": "Login successfully!",
            "user": {
                "id": 1,
                "username": self.username,
                "email": self.email
            },
        }
        self.assertEqual(resp.data, response_data)

    def test_login_cookies_set(self):
        resp = self.client.post(self.login_url, data={"username": self.username, "password": self.password}, format="json")
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)

        access_cookie = resp.cookies["access_token"]
        refresh_cookie = resp.cookies["refresh_token"]

        self.assertEqual(access_cookie["samesite"], self.expected_samesite)
        self.assertEqual(refresh_cookie["samesite"], self.expected_samesite)

        self.assertEqual(access_cookie["secure"], self.expected_secure)
        self.assertEqual(refresh_cookie["secure"], self.expected_secure)

        self.assertEqual(access_cookie["httponly"], self.expected_httponly)
        self.assertEqual(refresh_cookie["httponly"], self.expected_httponly)

    def test_client_stores_cookie_for_next_requests(self):
        """Optional: Prüfen, dass der Testclient die Cookies übernimmt (falls du Cookie-Auth nutzt)."""
        resp = self.client.post(self.login_url, {"username": self.username, "password": self.password}, format="json")
     
        self.assertIn("access_token", self.client.cookies)
        self.assertTrue(self.client.cookies["access_token"].value)

    def test_login_nonexistent_user(self):
        resp = self.client.post(self.login_url, {"username": "nope", "password": "pass1234"}, format="json")
        assert resp.status_code == 401

    def test_login_blacklists_previous_refresh(self):
  
        r1 = self.client.post(self.login_url, {"username": self.username, "password": self.password}, format="json")
        assert r1.status_code == 200
   
        r2 = self.client.post(self.login_url, {"username": self.username, "password": self.password}, format="json")
        assert r2.status_code == 200
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        user_tokens = OutstandingToken.objects.filter(user__username=self.username)
        assert BlacklistedToken.objects.filter(token__in=user_tokens).exists()


class Tests_of_Logout(APITestCase):
    '''Tests for the user logout endpoint.'''
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.username = "alice_login"
        self.email = "alice_login@example.com"
        self.password = "pass1234"
        
        User.objects.create_user(username=self.username, email=self.email, password=self.password)

        self.expected_samesite = "Lax"
        self.expected_secure = True
        self.expected_httponly = True
        self.client.post(self.login_url, data={"username": self.username, "password": self.password}, format="json")

    def test_logout_successful(self):
        resp = self.client.post(self.logout_url,data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_response(self):
        resp = self.client.post(self.logout_url,data={}, format="json")
        response_data = {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}
        self.assertEqual(resp.data, response_data)

    def test_logout_cookies_deleted(self):
        resp = self.client.post(self.logout_url,data={}, format="json")
        
        access_cookie = resp.cookies.get("access_token")
        refresh_cookie = resp.cookies.get("refresh_token")

        self.assertIsNotNone(access_cookie)
        self.assertIsNotNone(refresh_cookie)

        self.assertEqual(access_cookie.value, "")
        self.assertEqual(refresh_cookie.value, "")     

    def test_logout_allowed_with_only_refresh_cookie(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password}, format="json")
        self.client.cookies.pop("access_token", None)
        resp = self.client.post(self.logout_url, {}, format="json")
        assert resp.status_code == 200

    def test_logout_forbidden_without_any_tokens(self):
        self.client.cookies.clear()
        resp = self.client.post(self.logout_url, {}, format="json")
        assert resp.status_code == 401

    def test_logout_invalid_refresh_is_ignored_but_deletes_cookies(self):
        self.client.cookies["refresh_token"] = "invalid"
        resp = self.client.post(self.logout_url, {}, format="json")
        assert resp.status_code == 200
        assert resp.cookies["access_token"].value == ""
        assert resp.cookies["access_token"]["max-age"] in ("0", 0)
        assert resp.cookies["refresh_token"].value == ""
        assert resp.cookies["refresh_token"]["max-age"] in ("0", 0)

    def test_logout_blacklist_tokenerror_is_handled(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password}, format="json")
        with patch("rest_framework_simplejwt.tokens.RefreshToken.blacklist") as bl:
            from rest_framework_simplejwt.exceptions import TokenError
            bl.side_effect = TokenError("already blacklisted")
            resp = self.client.post(self.logout_url, {}, format="json")
        assert resp.status_code == 200
 

class Tests_of_Token_Refresh(APITestCase):
    '''Tests for the token refresh endpoint.'''
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.refresh_url = reverse("token_refresh")

        self.username = "alice_login"
        self.email = "alice_login@example.com"
        self.password = "pass1234"
        User.objects.create_user(username=self.username, email=self.email, password=self.password)

        login_resp = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK, getattr(login_resp, "data", login_resp))

        self.assertIn("access_token", self.client.cookies)
        self.assertIn("refresh_token", self.client.cookies)

        self.initial_access = self.client.cookies["access_token"].value
        self.initial_refresh = self.client.cookies["refresh_token"].value

    def test_token_refresh_successful(self):
        resp = self.client.post(self.refresh_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_token_refresh_response(self):
        resp = self.client.post(self.refresh_url, data={}, format="json")
        response_data = {
                            "detail": "Token refreshed",
                            "access": "new_access_token"
                        }   
        self.assertEqual(resp.data, response_data)
    
    def test_refresh_with_missing_access_cookie_creates_new_access_cookie(self):
        """
        Delete access cookie from client and then refresh.
        Expectation: 200 + new access_token cookie (value != initial_access).
        """
        self.client.cookies.pop("access_token", None)

        resp = self.client.post(self.refresh_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn("access_token", resp.cookies)
        new_access = resp.cookies["access_token"].value
        self.assertTrue(new_access)
        self.assertNotEqual(new_access, self.initial_access)

        if "refresh_token" in resp.cookies:
            new_refresh = resp.cookies["refresh_token"].value
            self.assertTrue(new_refresh)
            self.assertNotEqual(new_refresh, self.initial_refresh)
        else:
            self.assertEqual(self.client.cookies["refresh_token"].value, self.initial_refresh)

    def test_refresh_without_refresh_cookie_fails(self):
        """
        If the refresh_token cookie is missing, the refresh should fail.
        Expectation: 401 (or 400 depending on the implementation).
        """
        self.client.cookies.pop("access_token", None)
        self.client.cookies.pop("refresh_token", None)

        resp = self.client.post(self.refresh_url, data={}, format="json")

        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST), getattr(resp, "data", resp))

        self.assertNotIn("access_token", resp.cookies)
        self.assertNotIn("refresh_token", resp.cookies)

    def test_refresh_sets_new_access_even_if_access_cookie_present(self):
        """
        Some implementations always set a new access_token, even if one is already present.
        This test accepts both variants:
         - Either a new access_token is set (and overwrites),
         - or the server does not set a new one (then it remains unchanged).
        """
        resp = self.client.post(self.refresh_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, getattr(resp, "data", resp))

        if "access_token" in resp.cookies:
            new_access = resp.cookies["access_token"].value
            self.assertTrue(new_access)
        else:
            self.assertIn("access_token", self.client.cookies)
            self.assertTrue(self.client.cookies["access_token"].value)

    def test_refresh_response_shape_is_sane(self):
        """
        Testing the response data structure of the token refresh endpoint.
        """
        resp = self.client.post(self.refresh_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, getattr(resp, "data", resp))

        if hasattr(resp, "data") and isinstance(resp.data, dict):
            if "detail" in resp.data:
                self.assertIn("refresh", resp.data["detail"].lower())
            if "access" in resp.data:
                self.assertTrue(isinstance(resp.data["access"], str) and resp.data["access"])