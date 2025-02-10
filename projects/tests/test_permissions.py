from django.utils import timezone
from django.test import TestCase
from projects.permissions import IsProjectTechLeader, CanViewProject
from projects.models import Project
from users.models import User
from rest_framework.test import APIRequestFactory


class IsProjectTechLeaderPermissionTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        self.project = Project.objects.create(
            name="Project Permission Test",
            description="Test project for permissions",
            tech_leader=self.tech_leader,
            estimated_hours=100,
            start_date="2099-01-01",
            end_date="2099-02-01",
            status="PLANNING",
        )
        self.permission = IsProjectTechLeader()

    def test_permission_allows_tech_leader(self):
        request = self.factory.get("/")
        request.user = self.tech_leader
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.project)
        )

    def test_permission_denies_developer(self):
        request = self.factory.get("/")
        request.user = self.developer
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.project)
        )


class CanViewProjectPermissionTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.staff = User.objects.create_user(
            email="staff@example.com", password="password123", user_type="DEV"
        )
        self.staff.is_staff = True
        self.staff.save()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        self.project = Project.objects.create(
            name="Project View Test",
            description="Test project for view permissions",
            tech_leader=self.tech_leader,
            estimated_hours=120,
            start_date="2099-01-01",
            end_date="2099-03-01",
            status="PLANNING",
        )
        # Simula que o desenvolvedor está alocado
        self.project.developers.add(
            self.developer,
            through_defaults={
                "hours_per_month": 40,
                "start_date": timezone.localdate(),
                "end_date": timezone.localdate() + timezone.timedelta(days=30),
                "stack": self.project.stacks.first(),  # Ensure a stack is provided
            },
        )
        self.permission = CanViewProject()

    def test_view_permission_staff(self):
        request = self.factory.get("/")
        request.user = self.staff
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.project)
        )

    def test_view_permission_tech_leader(self):
        request = self.factory.get("/")
        request.user = self.tech_leader
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.project)
        )

    def test_view_permission_developer_allocated(self):
        request = self.factory.get("/")
        request.user = self.developer
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.project)
        )

    def test_view_permission_denied_for_random_user(self):
        random_user = User.objects.create_user(
            email="random@example.com", password="password123", user_type="DEV"
        )
        request = self.factory.get("/")
        request.user = random_user
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.project)
        )
