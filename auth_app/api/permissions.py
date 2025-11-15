
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import exceptions

class HasRefreshTokenAuth(BasePermission):
    """
    Permission class that checks for a valid refresh token in cookies.
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