from rest_framework import permissions


class CanAssignStackPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type == "TL":
            return True
        target_user_id = request.data.get("user")
        if target_user_id:
            return str(request.user.id) == str(target_user_id)
        return True
