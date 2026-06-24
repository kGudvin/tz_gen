from rest_framework import permissions


class IsApprovedUser(permissions.BasePermission):
    message = "Аккаунт ожидает одобрения администратора"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_approved))


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user_id == request.user.id

