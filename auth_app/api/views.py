from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .permissions import HasValidJWTForLogout, HasRefreshTokenAuth
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
            user = serializer.validated_data["user"]

            response = Response({"detail": "Login successfully", "user": user})

            response.set_cookie(
                key='access_token',
                value=str(access),
                httponly=True,
                secure=True,  
                samesite='Lax'  
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=True,  
                samesite='Lax'  
            )

            return response

        except Exception as e:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [HasValidJWTForLogout]
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
    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get('access')

        response = Response(
            {   "detail": "Token refreshed",
                "access": "new_access_token"
            },)
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,  
            samesite='Lax'  
        )
        return response