from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework import exceptions

class CookieJWTAuthentication(JWTAuthentication):
    """
    Authentifiziert über Cookie 'access_token'.
    Fällt zurück auf Standard-Header, wenn kein Cookie vorhanden.
    """
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token:
            try:
                validated = self.get_validated_token(raw_token)
                user = self.get_user(validated)
                return (user, validated)
            except InvalidToken:
                raise exceptions.AuthenticationFailed("Invalid access token.")
        return super().authenticate(request)
