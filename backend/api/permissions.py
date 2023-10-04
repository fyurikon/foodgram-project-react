from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrAuthorOrReadOnly(BasePermission):
    """Permission only for Admin and Author."""
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_staff
            or (obj.author == request.user)
        )
