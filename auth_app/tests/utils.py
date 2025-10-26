from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

def create_user(username="alice",email="alice@example.com", password="pass1234", **extra):
    """
    Legt einen User in der Test-Datenbank an und setzt ein Passwort.
    """
    user = User.objects.create_user(username=username, email=email, password=password, **extra)
    return user

def make_access_token_for_user(user) -> str:
    """
    Erzeugt ein gültiges JWT access_token für den gegebenen User.
    Achtung: Das Token ist zeitlich gültig gemäß SIMPLE_JWT Einstellungen.
    """
    token = AccessToken.for_user(user)
    return str(token)