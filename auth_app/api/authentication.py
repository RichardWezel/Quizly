from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    '''Authenticates users based on JWT tokens stored in cookies.'''
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token:
            try:
                validated = self.get_validated_token(raw_token)
                user = self.get_user(validated)
                return (user, validated)
            except InvalidToken:
                # Früher: raise AuthenticationFailed(...)
                # Jetzt: weich zurückfallen lassen – die Permission entscheidet
                return None
        return super().authenticate(request)
