from django.test import TestCase
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from projects.models import Project, ProjectStack
from projects.serializers import (
    ProjectSerializer,
    ProjectDeveloperSerializer,
    ProjectStackSerializer,
)
from users.models import User
from stacks.models import Stack


class ProjectSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # Cria Tech Leader e atribui uma stack
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack1 = Stack.objects.create(name="Django", description="Web framework")
        self.tech_leader.user_stacks.create(
            stack=self.stack1,
            proficiency_level="ADV",
            years_of_experience=5,
            is_primary=True,
        )
        self.start_date = date.today() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=30)
        self.project = Project.objects.create(
            name="Project Serializer Test",
            description="Testing project serializer",
            tech_leader=self.tech_leader,
            estimated_hours=200,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        self.project.stacks.add(self.stack1)

    def test_project_serializer_fields(self):
        serializer = ProjectSerializer(instance=self.project)
        data = serializer.data
        self.assertEqual(data["name"], self.project.name)
        self.assertEqual(data["tech_leader"], self.tech_leader.id)
        # Sem desenvolvedores, total_hours deve ser 0
        self.assertEqual(data["total_hours"], 0)

    def test_project_serializer_invalid_dates(self):
        # Testa validação de datas: start_date > end_date
        data = {
            "name": "Invalid Dates",
            "description": "Test",
            "tech_leader": self.tech_leader.id,
            "estimated_hours": 150,
            "start_date": self.end_date.isoformat(),  # invertido
            "end_date": self.start_date.isoformat(),
            "status": "PLANNING",
        }
        serializer = ProjectSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        # Pode aparecer o erro em non_field_errors ou em um campo específico
        self.assertTrue(
            "end_date" in str(context.exception)
            or "non_field_errors" in str(context.exception)
        )

    def test_project_serializer_invalid_tech_leader(self):
        # Tenta atribuir um desenvolvedor como tech_leader
        developer = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        data = {
            "name": "Invalid TL",
            "description": "Test",
            "tech_leader": developer.id,
            "estimated_hours": 150,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": "PLANNING",
        }
        serializer = ProjectSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("tech_leader", context.exception.detail)


class ProjectDeveloperSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            user_type="DEV",
            monthly_hours=160,
        )
        self.stack1 = Stack.objects.create(
            name="React", description="Front-end framework"
        )
        self.developer.user_stacks.create(
            stack=self.stack1,
            proficiency_level="INT",
            years_of_experience=3,
            is_primary=True,
        )
        self.start_date = date.today() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=20)
        self.project = Project.objects.create(
            name="Project Developer Serializer Test",
            description="Test project",
            tech_leader=self.tech_leader,
            estimated_hours=300,
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=45),
            status="PLANNING",
        )
        self.project.stacks.add(self.stack1)
        self.context = {"project": self.project}
        self.project.stacks.add(
            self.stack1, through_defaults={"required_developers": 2}
        )

    def test_project_developer_serializer_valid(self):
        data = {
            "developer": self.developer.id,
            "stack": self.stack1.id,
            "hours_per_month": 50,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_by": self.tech_leader.id,
            "updated_by": self.tech_leader.id
        }
        serializer = ProjectDeveloperSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_project_developer_serializer_invalid_dates(self):
        data = {
            "developer": self.developer.id,
            "stack": self.stack1.id,
            "hours_per_month": 50,
            "start_date": self.end_date.isoformat(),
            "end_date": self.start_date.isoformat(),
        }
        serializer = ProjectDeveloperSerializer(data=data, context=self.context)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("end_date", str(context.exception))


class ProjectStackSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack1 = Stack.objects.create(name="Vue", description="Frontend framework")
        self.tech_leader.user_stacks.create(
            stack=self.stack1,
            proficiency_level="ADV",
            years_of_experience=4,
            is_primary=True,
        )
        self.project = Project.objects.create(
            name="Project Stack Serializer Test",
            description="Test project for stack serializer",
            tech_leader=self.tech_leader,
            estimated_hours=120,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=25),
            status="PLANNING",
        )
        self.context = {"project": self.project}

    def test_project_stack_serializer_valid(self):
        data = {"stack": self.stack1.id, "required_developers": 2}
        serializer = ProjectStackSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.required_developers, 2)

    def test_project_stack_serializer_invalid_tech_leader_stack(self):
        new_stack = Stack.objects.create(
            name="Angular", description="Another framework"
        )
        data = {"stack": new_stack.id, "required_developers": 1}
        serializer = ProjectStackSerializer(data=data, context=self.context)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("stack", context.exception.detail)
