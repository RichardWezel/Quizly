
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class HasValidJWTForLogout(BasePermission):
    """
    Erlaubt Zugriff, wenn ein gültiges Access- ODER Refresh-Token im Cookie liegt.
    """
    def has_permission(self, request, view):
        # Access prüfen
        access = request.COOKIES.get('access_token')
        if access:
            try:
                JWTAuthentication().get_validated_token(access)
                return True
            except InvalidToken:
                pass

        # Refresh prüfen
        refresh = request.COOKIES.get('refresh_token')
        if refresh:
            try:
                # Konstruktor validiert Signatur/Expiry
                RefreshToken(refresh)
                return True
            except TokenError:
                pass

        return False
