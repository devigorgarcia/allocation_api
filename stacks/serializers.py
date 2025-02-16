from rest_framework import serializers
from users.models import User
from .models import Stack, UserStack


class StackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stack
        fields = ["id", "name", "description", "is_active"]


class UserStackSerializer(serializers.ModelSerializer):
    stack_name = serializers.CharField(source="stack.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_type = serializers.CharField(source="user.user_type", read_only=True)

    class Meta:
        model = UserStack
        fields = [
            "id",
            "user_email",
            "user_username",
            "user_type",
            "stack",
            "stack_name",
            "proficiency_level",
            "years_of_experience",
            "is_primary",
        ]
        read_only_fields = ["stack_name", "user_email", "user_type", "user_username"]


class AddUserStackSerializer(serializers.ModelSerializer):
    stack_name = serializers.CharField(source="stack.name", read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        default=serializers.CurrentUserDefault(),
        help_text="ID do usuário que receberá a stack (apenas para admin/TL)",
    )

    class Meta:
        model = UserStack
        fields = [
            "user",
            "stack",
            "stack_name",
            "proficiency_level",
            "years_of_experience",
            "is_primary",
        ]
        read_only_fields = ["stack_name"]

    def validate(self, data):
        request = self.context["request"]
        current_user = request.user

        if not (current_user.is_staff or current_user.is_tech_leader()):
            data["user"] = current_user

        target_user = data.get("user", current_user)
        stack = data["stack"]

        if UserStack.objects.filter(user=target_user, stack=stack).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        f"O usuário {target_user.email} já possui a stack {stack.name} com nível já atribuído."
                    ]
                }
            )

        if data.get("is_primary"):
            if UserStack.objects.filter(user=target_user, is_primary=True).exists():
                raise serializers.ValidationError(
                    {
                        "is_primary": (
                            f"O usuário {target_user.email} já possui uma stack primária. Desmarque-a primeiro."
                        )
                    }
                )

        return data
