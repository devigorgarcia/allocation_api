# users/tests/test_permissions.py
from django.test import TestCase, RequestFactory
from users.models import User
from users.permissions import IsTechLeaderOrSelf


class IsTechLeaderOrSelfTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsTechLeaderOrSelf()
        self.tech_leader = User.objects.create_user(
            email="tech@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )

    def test_tech_leader_has_permission(self):
        request = self.factory.get("/")
        request.user = self.tech_leader
        # Tech Leader deve ter permissão para acessar qualquer usuário
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.developer)
        )

    def test_developer_accessing_self(self):
        request = self.factory.get("/")
        request.user = self.developer
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.developer)
        )

    def test_developer_accessing_other(self):
        request = self.factory.get("/")
        request.user = self.developer
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.tech_leader)
        )
