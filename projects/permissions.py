from rest_framework import permissions


class IsProjectTechLeader(permissions.BasePermission):
    """
    Permite acesso apenas ao Tech Leader do projeto.
    """

    def has_object_permission(self, request, view, obj):
        return obj.tech_leader == request.user or request.user.is_superuser


class CanViewProject(permissions.BasePermission):
    """
    Permite visualização para Tech Leaders e desenvolvedores alocados.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in permissions.SAFE_METHODS:
            return (
                user.is_staff
                or obj.tech_leader == user
                or obj.projectdeveloper_set.filter(developer=user).exists()
            )

        return user.is_staff or obj.tech_leader == user
