from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


# stacks/permissions.py
from rest_framework import permissions


class CanAssignStackPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.is_tech_leader():
            return True

        target_user_id = request.data.get("user")
        if target_user_id:
            # Se um usuário alvo foi especificado, verifica se é o próprio usuário
            return str(request.user.id) == str(target_user_id)

        # Se nenhum usuário foi especificado, assume que é para o próprio usuário
        return True
