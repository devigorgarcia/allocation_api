from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from projects import serializers
from stacks.models import Stack, UserStack
from stacks.serializers import (
    StackSerializer,
    UserStackSerializer,
    AddUserStackSerializer,
)
from users.models import User


class StackSerializerTest(TestCase):
    def setUp(self):
        self.stack = Stack.objects.create(name="Django", description="A web framework")

    def test_stack_serializer(self):
        serializer = StackSerializer(instance=self.stack)
        data = serializer.data
        self.assertEqual(data["name"], "Django")
        self.assertEqual(data["description"], "A web framework")
        self.assertIn("is_active", data)


class UserStackSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password123", user_type="DEV"
        )
        self.stack = Stack.objects.create(
            name="Python", description="Programming language"
        )
        self.user_stack = UserStack.objects.create(
            user=self.user,
            stack=self.stack,
            proficiency_level="EXP",
            years_of_experience=4,
            is_primary=True,
        )

    def test_userstack_serializer(self):
        serializer = UserStackSerializer(instance=self.user_stack)
        data = serializer.data
        self.assertEqual(data["user"], self.user.id)
        self.assertEqual(data["stack"], self.stack.id)
        self.assertEqual(data["stack_name"], self.stack.name)
        self.assertEqual(data["user_email"], self.user.email)
        self.assertEqual(data["proficiency_level"], "EXP")
        self.assertEqual(data["years_of_experience"], 4)
        self.assertTrue(data["is_primary"])


class AddUserStackSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.developer = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        self.tech_leader = User.objects.create_user(
            email="tech@example.com", password="password123", user_type="TL"
        )
        self.stack = Stack.objects.create(name="Django", description="A web framework")

    def get_serializer_context(self, user):
        request = self.factory.post("/")
        request.user = user
        return {"request": request}

    def test_developer_cannot_assign_stack_to_other_user(self):
        """
        Mesmo que um desenvolvedor envie um valor de "user" diferente,
        o serializer deve sobrescrever e usar o próprio usuário.
        """
        data = {
            "user": self.tech_leader.id,
            "stack": self.stack.id,
            "proficiency_level": "INT",
            "years_of_experience": 2,
            "is_primary": False,
        }
        serializer = AddUserStackSerializer(
            data=data, context=self.get_serializer_context(self.developer)
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.user, self.developer)

    def test_tech_leader_can_assign_stack_to_other_user(self):
        """
        Tech Leader pode associar uma stack a outro usuário.
        """
        data = {
            "user": self.developer.id,
            "stack": self.stack.id,
            "proficiency_level": "ADV",
            "years_of_experience": 3,
            "is_primary": False,
        }
        serializer = AddUserStackSerializer(
            data=data, context=self.get_serializer_context(self.tech_leader)
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.user, self.developer)
        self.assertEqual(instance.stack, self.stack)

    def test_developer_assign_stack_without_specifying_user(self):
        """
        Mesmo que um desenvolvedor envie o campo "user", o serializer deve usar o próprio usuário autenticado.
        """
        data = {
            "stack": self.stack.id,
            "proficiency_level": "BEG",
            "years_of_experience": 1,
            "is_primary": False,
            "user": self.tech_leader.id,
        }
        serializer = AddUserStackSerializer(
            data=data, context=self.get_serializer_context(self.developer)
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.user, self.developer)

    def test_cannot_assign_duplicate_stack(self):
        """
        Testa que o serializer impede a criação de uma associação duplicada (mesmo usuário e mesma stack).
        """
        # Cria uma associação inicial
        UserStack.objects.create(
            user=self.developer,
            stack=self.stack,
            proficiency_level="ADV",
            years_of_experience=3,
            is_primary=False,
        )
        data = {
            "stack": self.stack.id,
            "proficiency_level": "ADV",
            "years_of_experience": 3,
            "is_primary": False,
        }
        serializer = AddUserStackSerializer(
            data=data, context=self.get_serializer_context(self.developer)
        )
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        errors = context.exception.detail
        # Verifica que os erros foram lançados em "non_field_errors"
        self.assertIn("non_field_errors", errors)

    def test_primary_stack_validation(self):
        """
        Verifica que, se o usuário já possui uma stack primária, não é possível criar outra.
        """
        # Cria uma associação primária inicial
        UserStack.objects.create(
            user=self.developer,
            stack=self.stack,
            proficiency_level="ADV",
            years_of_experience=3,
            is_primary=True,
        )
        new_stack = Stack.objects.create(
            name="Python", description="Programming language"
        )
        data = {
            "stack": new_stack.id,
            "proficiency_level": "INT",
            "years_of_experience": 2,
            "is_primary": True,
        }
        serializer = AddUserStackSerializer(
            data=data, context=self.get_serializer_context(self.developer)
        )
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        errors = context.exception.detail
        self.assertIn("is_primary", errors)
