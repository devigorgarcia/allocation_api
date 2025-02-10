# projects/tests/test_views.py
from datetime import date, timedelta
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from projects.models import Project, ProjectDeveloper, ProjectStack
from users.models import User
from stacks.models import Stack
from django.utils import timezone


# ----- Teste para ProjectListCreateView -----
class ProjectListCreateViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Cria um Tech Leader e associa uma stack
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack = Stack.objects.create(name="Django", description="Web framework")
        # Certifique-se de que no método clean() do modelo Project seja usado values_list()
        self.tech_leader.user_stacks.create(
            stack=self.stack,
            proficiency_level="ADV",
            years_of_experience=5,
            is_primary=True,
        )
        self.start_date = date.today() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=30)
        self.url = reverse("projects:project-list-create")

    def test_list_projects_as_staff(self):
        # Cria um projeto para listagem
        Project.objects.create(
            name="Staff Project",
            description="Projeto para staff",
            tech_leader=self.tech_leader,
            estimated_hours=200,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        staff = User.objects.create_user(
            email="staff@example.com", password="password123", user_type="DEV"
        )
        staff.is_staff = True
        staff.save()
        self.client.force_authenticate(user=staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como a view é paginada, os resultados vêm na chave "results"
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_projects_as_tech_leader(self):
        project = Project.objects.create(
            name="TL Project",
            description="Projeto do Tech Leader",
            tech_leader=self.tech_leader,
            estimated_hours=150,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        self.client.force_authenticate(user=self.tech_leader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], project.name)

    def test_create_project(self):
        # Incluímos o tech_leader no payload para evitar erro de validação
        data = {
            "name": "New Project",
            "description": "Um novo projeto",
            "tech_leader": self.tech_leader.id,  # Necessário se o campo não for read-only
            "estimated_hours": 300,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": "PLANNING",
            "stacks": [],  # Sem stacks associadas inicialmente
        }
        self.client.force_authenticate(user=self.tech_leader)
        response = self.client.post(self.url, data, format="json")
        # Se tudo estiver correto, o projeto será criado
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tech_leader"], self.tech_leader.id)


# ----- Teste para ProjectDetailView -----
class ProjectDetailViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack = Stack.objects.create(name="Django", description="Web framework")
        self.tech_leader.user_stacks.create(
            stack=self.stack,
            proficiency_level="ADV",
            years_of_experience=5,
            is_primary=True,
        )
        self.start_date = date.today() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=30)
        self.project = Project.objects.create(
            name="Detail Project",
            description="Projeto para teste de detalhe",
            tech_leader=self.tech_leader,
            estimated_hours=250,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        self.project.stacks.add(self.stack)
        self.url = reverse("projects:project-detail", kwargs={"pk": self.project.id})

    def test_retrieve_project_detail_as_tech_leader(self):
        self.client.force_authenticate(user=self.tech_leader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.project.name)

    def test_update_project_detail(self):
        self.client.force_authenticate(user=self.tech_leader)
        data = {"name": "Updated Project Name", "stacks": []}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated Project Name")

    def test_delete_project_detail(self):
        self.client.force_authenticate(user=self.tech_leader)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(id=self.project.id)


# ----- Teste para ProjectDeveloper endpoints -----
class ProjectDeveloperCreateViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Cria TL, desenvolvedor e stack
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            user_type="DEV",
            monthly_hours=160,
        )
        self.stack = Stack.objects.create(
            name="React", description="Front-end framework"
        )
        self.developer.user_stacks.create(
            stack=self.stack,
            proficiency_level="INT",
            years_of_experience=3,
            is_primary=True,
        )
        self.project = Project.objects.create(
            name="Dev Allocation Project",
            description="Projeto para alocar desenvolvedores",
            tech_leader=self.tech_leader,
            estimated_hours=300,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
            status="PLANNING",
        )
        self.project.stacks.add(self.stack)
        self.url = reverse(
            "projects:project-developer-create", kwargs={"project_id": self.project.id}
        )
        self.client.force_authenticate(user=self.tech_leader)

    def test_create_project_developer_allocation(self):
        data = {
            "developer": self.developer.id,
            "stack": self.stack.id,
            "hours_per_month": 50,
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=40)).isoformat(),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verifica se a alocação foi criada
        self.assertTrue(
            self.project.projectdeveloper_set.filter(developer=self.developer).exists()
        )


class ProjectDeveloperListViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            user_type="DEV",
            monthly_hours=160,
        )
        self.stack = Stack.objects.create(
            name="React", description="Front-end framework"
        )
        self.developer.user_stacks.create(
            stack=self.stack,
            proficiency_level="INT",
            years_of_experience=3,
            is_primary=True,
        )
        self.project = Project.objects.create(
            name="Dev List Project",
            description="Projeto para listar alocações de desenvolvedores",
            tech_leader=self.tech_leader,
            estimated_hours=300,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
            status="PLANNING",
        )
        self.project.stacks.add(self.stack)
        # Cria uma alocação completa via .create() (evita usar .add())
        from projects.models import ProjectDeveloper

        ProjectDeveloper.objects.create(
            project=self.project,
            developer=self.developer,
            stack=self.stack,
            hours_per_month=50,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
        )
        self.url = reverse(
            "projects:project-developer-list", kwargs={"project_id": self.project.id}
        )
        self.client.force_authenticate(user=self.tech_leader)

    def test_list_project_developers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["developer"], self.developer.id)


class ProjectDeveloperDetailViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            user_type="DEV",
            monthly_hours=160,
        )
        self.stack = Stack.objects.create(
            name="React", description="Front-end framework"
        )
        self.developer.user_stacks.create(
            stack=self.stack,
            proficiency_level="INT",
            years_of_experience=3,
            is_primary=True,
        )
        self.project = Project.objects.create(
            name="Dev Detail Project",
            description="Projeto para detalhe de alocação",
            tech_leader=self.tech_leader,
            estimated_hours=300,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
            status="PLANNING",
        )
        self.project.stacks.add(self.stack)
        from projects.models import ProjectDeveloper

        self.allocation = ProjectDeveloper.objects.create(
            project=self.project,
            developer=self.developer,
            stack=self.stack,
            hours_per_month=50,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
        )
        self.url = reverse(
            "projects:project-developer-detail",
            kwargs={"project_id": self.project.id, "pk": self.allocation.id},
        )
        self.client.force_authenticate(user=self.tech_leader)

    def test_retrieve_project_developer_detail(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["developer"], self.developer.id)

    def test_update_project_developer_detail(self):
        data = {
            "hours_per_month": 60,
            "start_date": self.allocation.start_date.isoformat(),
            "end_date": self.allocation.end_date.isoformat(),
        }
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.allocation.refresh_from_db()
        self.assertEqual(self.allocation.hours_per_month, 60)

    def test_delete_project_developer_detail(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.project.projectdeveloper_set.filter(id=self.allocation.id).exists()
        )


# ----- Teste para ProjectStack endpoints -----
class ProjectStackCreateListViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack = Stack.objects.create(name="Vue", description="Frontend framework")
        self.tech_leader.user_stacks.create(
            stack=self.stack,
            proficiency_level="ADV",
            years_of_experience=4,
            is_primary=True,
        )
        self.project = Project.objects.create(
            name="Stack Project Test",
            description="Projeto para testar stacks",
            tech_leader=self.tech_leader,
            estimated_hours=150,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=35),
            status="PLANNING",
        )
        self.url_create = reverse(
            "projects:project-stack-create", kwargs={"project_id": self.project.id}
        )
        self.url_list = reverse(
            "projects:project-stack-list", kwargs={"project_id": self.project.id}
        )
        self.client.force_authenticate(user=self.tech_leader)

    def test_create_project_stack(self):
        data = {"stack": self.stack.id, "required_developers": 2}
        response = self.client.post(self.url_create, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["required_developers"], 2)

    def test_list_project_stacks(self):
        from projects.models import ProjectStack

        ProjectStack.objects.create(
            project=self.project, stack=self.stack, required_developers=2
        )
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
