from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

def create_user(username="alice",email="alice@example.com", password="pass1234", **extra):
    """Creates a user in the test database and sets a password."""
    user = User.objects.create_user(username=username, email=email, password=password, **extra)
    return user

def make_access_token_for_user(user) -> str:
    """
    Generates a valid JWT access token for the given user.
    Note: The token is valid according to SIMPLE_JWT settings.
    """
    token = AccessToken.for_user(user)
    return str(token)