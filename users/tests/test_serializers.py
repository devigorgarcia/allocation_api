# users/tests/test_serializers.py
from django.test import TestCase
from users.serializers import UserSerializer, UserDetailSerializer
from users.models import User


class UserSerializerTest(TestCase):
    def test_create_user(self):
        """
        Testa se o serializer cria o usuário corretamente e se a senha é setada.
        """
        data = {
            "email": "alice@example.com",
            "username": "alice",
            "user_type": "DEV",
            "password": "password123",
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.user_type, data["user_type"])
        self.assertTrue(user.check_password(data["password"]))


class UserDetailSerializerTest(TestCase):
    def test_total_stacks_calculation(self):
        """
        Como o usuário criado não possui stacks, total_stacks deve ser 0.
        """
        user = User.objects.create_user(
            email="bob@example.com", password="password123", user_type="DEV"
        )
        serializer = UserDetailSerializer(instance=user)
        self.assertEqual(serializer.data["total_stacks"], 0)
