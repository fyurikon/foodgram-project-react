from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrAuthorOrReadOnly(BasePermission):
    """Permission only for Admin and Author."""
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user.is_staff
