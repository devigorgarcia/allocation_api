from django.test import TestCase
from stacks.models import Stack, UserStack
from users.models import User


class StackModelTest(TestCase):
    def setUp(self):
        self.stack1 = Stack.objects.create(name="Django", description="Web framework")
        self.stack2 = Stack.objects.create(
            name="Python", description="Programming language"
        )

    def test_stack_str(self):
        """Testa o método __str__ do modelo Stack."""
        self.assertEqual(str(self.stack1), "Django")
        self.assertEqual(str(self.stack2), "Python")

    def test_stack_ordering(self):
        """Verifica se a ordenação (por nome) está correta."""
        stacks = list(Stack.objects.all())
        # Pela ordenação definida (ordering = ['name']), 'Django' deve vir antes de 'Python'
        self.assertEqual(stacks[0].name, "Django")
        self.assertEqual(stacks[1].name, "Python")


class UserStackModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password123", user_type="DEV"
        )
        self.stack1 = Stack.objects.create(name="Django", description="Web framework")
        self.stack2 = Stack.objects.create(
            name="Python", description="Programming language"
        )
        # Cria uma associação com is_primary=True
        self.userstack1 = UserStack.objects.create(
            user=self.user,
            stack=self.stack1,
            proficiency_level="ADV",
            years_of_experience=3,
            is_primary=True,
        )

    def test_userstack_str(self):
        """Verifica o método __str__ do modelo UserStack."""
        expected_str = f"{self.user.email} - {self.stack1.name} ({self.userstack1.get_proficiency_level_display()})"
        self.assertEqual(str(self.userstack1), expected_str)

    def test_primary_update(self):
        """
        Testa que, ao salvar uma nova associação com is_primary=True,
        qualquer outra associação anterior do mesmo usuário com is_primary=True seja desmarcada.
        """
        # Cria uma segunda associação com is_primary=True para o mesmo usuário
        userstack2 = UserStack.objects.create(
            user=self.user,
            stack=self.stack2,
            proficiency_level="INT",
            years_of_experience=2,
            is_primary=True,
        )
        # Recarrega a associação anterior do banco de dados
        self.userstack1.refresh_from_db()
        self.assertFalse(self.userstack1.is_primary)
        self.assertTrue(userstack2.is_primary)
