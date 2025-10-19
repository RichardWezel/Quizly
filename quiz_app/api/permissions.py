from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    message = "Only the Owner of Quiz can do changes."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id == getattr(request.user, 'id', None)