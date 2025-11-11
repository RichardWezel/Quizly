from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from datetime import datetime, timezone
from .permissions import HasRefreshTokenAuth
from .authentication import CookieJWTAuthentication
from .serializers import RegistrationSerializer, LoginSerializer

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            data = {
                'username': saved_account.username,
                'email': saved_account.email,
                'user_id': saved_account.pk
            }
            return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            refresh = serializer.validated_data["refresh"]
            access = serializer.validated_data["access"]
            user = serializer.user 


            # Token-Objekte erzeugen, um jti und Ablaufzeiten zu lesen
            refresh_obj = RefreshToken(refresh)
            access_obj  = AccessToken(access)

            for token in OutstandingToken.objects.filter(user=user).exclude(jti=refresh_obj["jti"]):
                BlacklistedToken.objects.get_or_create(token=token)

            # Cookie-Laufzeiten (in Sekunden bis Ablauf)
            now_ts = int(datetime.now(timezone.utc).timestamp())
            access_max_age = int(access_obj["exp"]) - now_ts
            refresh_max_age = int(refresh_obj["exp"]) - now_ts

            response = Response(
                {   "detail": "Login successfully!",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                },
                    status=status.HTTP_200_OK
            )

            response.set_cookie(
                key='access_token',
                value=str(access),
                httponly=True,
                secure=False,  
                samesite='Lax',
                max_age=access_max_age  
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,  
                samesite='Lax',
                max_age=refresh_max_age
            )

            return response

        except Exception as e:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()  
                except TokenError:
                          # z.B. schon abgelaufen/invalid – ignorieren, wir löschen eh die Cookies
                    pass

            response = Response(
                {
                    "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
                },
                status=status.HTTP_200_OK
            )


            response.delete_cookie('access_token', path='/', samesite='Lax') 
            response.delete_cookie('refresh_token', path='/', samesite='Lax') 

            return response

        except Exception:
            return Response({"detail": "Internal Server Error"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [HasRefreshTokenAuth]

    def post(self, request, *args, **kwargs):
        try: 
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response(
                    {"detail": "Refresh token not found"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)

            access_token = serializer.validated_data.get('access')
            new_refresh  = serializer.validated_data.get('refresh')  # kann None sein, je nach Settings

            resp = Response({"detail": "Token refreshed"}, status=200)
            resp.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True, secure=False, samesite='Lax', path='/'
            )
            if new_refresh:
                resp.set_cookie(
                    key='refresh_token',
                    value=new_refresh,
                    httponly=True, secure=False, samesite='Lax', path='/'
                )
            return resp
        
        except (InvalidToken, TokenError):
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception:
            return Response(
                {"detail": "Internal Server Error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )