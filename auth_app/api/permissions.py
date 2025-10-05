
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions



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

class HasRefreshTokenAuth(BasePermission):
    """
    Erlaubt Zugriff, wenn ein gültiger Refresh-Token im Cookie liegt.
    Fehlt/ist er ungültig -> 401 (NotAuthenticated), nicht 403.
    """
    def has_permission(self, request, view):
        refresh = request.COOKIES.get('refresh_token')
        if not refresh:
            raise exceptions.NotAuthenticated(detail="Refresh token not found or invalid")

        try:
            RefreshToken(refresh)
            return True
        except TokenError:
            raise exceptions.NotAuthenticated(detail="Invalid refresh token")