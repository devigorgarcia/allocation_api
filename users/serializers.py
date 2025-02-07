# users/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from stacks.models import UserStack
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "user_type", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            user_type=validated_data["user_type"],
            password=validated_data["password"],
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"


class UserStackInUserSerializer(serializers.ModelSerializer):

    stack_name = serializers.CharField(source="stack.name", read_only=True)

    class Meta:
        model = UserStack
        fields = [
            "stack_name",
            "proficiency_level",
            "years_of_experience",
            "is_primary",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado para usuários, incluindo suas stacks
    """

    user_stacks = UserStackInUserSerializer(many=True, read_only=True)
    total_stacks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "user_type",
            "user_stacks",
            "total_stacks",
        ]

    def get_total_stacks(self, obj):
        """
        Método que calcula o total de stacks do usuário
        """
        return obj.user_stacks.count()
