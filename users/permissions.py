# users/permissions.py
from rest_framework import permissions


class IsTechLeaderOrSelf(permissions.BasePermission):
    """
    Permissão customizada que permite que:
    - Tech Leaders vejam todos os usuários
    - Desenvolvedores vejam apenas seu próprio perfil
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_tech_leader() or request.user.is_superuser:
            return True

        return obj.id == request.user.id
