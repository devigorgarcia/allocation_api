from django.test import TestCase
from users.models import User


class UserModelTest(TestCase):
    def test_username_auto_generation(self):
        """
        Verifica se, ao criar um usuário sem informar username,
        o username é gerado a partir do email.
        """
        email = "john@example.com"
        user = User.objects.create_user(
            email=email, password="password123", user_type="DEV"
        )
        self.assertEqual(user.username, "john")

    def test_is_tech_leader_and_developer_methods(self):
        """
        Verifica se os métodos is_tech_leader e is_developer funcionam corretamente.
        """
        user_tl = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        user_dev = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )

        self.assertTrue(user_tl.is_tech_leader())
        self.assertFalse(user_tl.is_developer())
        self.assertTrue(user_dev.is_developer())
        self.assertFalse(user_dev.is_tech_leader())
