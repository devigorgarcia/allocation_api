from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from projects.models import Project, ProjectDeveloper, ProjectStack, ProjectChangeLog
from users.models import User
from stacks.models import Stack
from core.exceptions import ProjectValidationError


class ProjectModelTest(TestCase):
    def setUp(self):
        # Cria um Tech Leader e o atribui a uma stack
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack1 = Stack.objects.create(name="Django", description="Web framework")
        # Atribui a stack ao Tech Leader
        self.tech_leader.user_stacks.create(
            stack=self.stack1,
            proficiency_level="ADV",
            years_of_experience=5,
            is_primary=True,
        )
        self.start_date = date.today() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=30)

    def test_project_str(self):
        project = Project.objects.create(
            name="Project A",
            description="Test project",
            tech_leader=self.tech_leader,
            estimated_hours=100,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        expected_str = f"Project A - {self.tech_leader.email}"
        self.assertEqual(str(project), expected_str)

    def test_project_clean_invalid_dates(self):
        # Verifica se a validação dispara quando a data de início é posterior à de término
        project = Project(
            name="Project Invalid",
            description="Invalid dates",
            tech_leader=self.tech_leader,
            estimated_hours=50,
            start_date=self.end_date,  # Datas invertidas
            end_date=self.start_date,
            status="PLANNING",
        )
        with self.assertRaises(ValidationError) as cm:
            project.clean()
        self.assertIn("end_date", cm.exception.message_dict)

    def test_project_clean_missing_tech_leader_stacks(self):
        # Cria um tech leader que não possui nenhuma stack atribuída
        tl_no_stack = User.objects.create_user(
            email="tl2@example.com", password="password123", user_type="TL"
        )
        project = Project(
            name="Project Missing Stacks",
            description="Tech Leader missing stacks",
            tech_leader=tl_no_stack,
            estimated_hours=80,
            start_date=self.start_date,
            end_date=self.end_date,
            status="PLANNING",
        )
        project.save()  # É necessário salvar para manipular M2M
        project.stacks.add(self.stack1)
        with self.assertRaises(ProjectValidationError) as cm:
            project.clean()
        self.assertIn(
            "Tech Leader não possui todas as stacks necessárias", str(cm.exception)
        )


class ProjectDeveloperModelTest(TestCase):
    def setUp(self):
        # Cria um Tech Leader e um Desenvolvedor
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.developer = User.objects.create_user(
            email="dev@example.com",
            password="password123",
            user_type="DEV",
            monthly_hours=160,
        )
        # Cria uma stack e atribui ao desenvolvedor
        self.stack1 = Stack.objects.create(
            name="React", description="Front-end framework"
        )
        self.developer.user_stacks.create(
            stack=self.stack1,
            proficiency_level="INT",
            years_of_experience=3,
            is_primary=True,
        )
        # Cria um projeto e associa a stack
        self.project = Project.objects.create(
            name="Project Dev Allocation",
            description="Test project for developer",
            tech_leader=self.tech_leader,
            estimated_hours=200,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
            status="PLANNING",
        )
        self.project.stacks.add(self.stack1)

    def test_project_developer_clean_invalid_dates(self):
        # Testa se a alocação com data de início no passado dispara validação
        pd = ProjectDeveloper(
            project=self.project,
            developer=self.developer,
            hours_per_month=50,
            stack=self.stack1,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=20),
        )
        with self.assertRaises(ValidationError) as cm:
            pd.clean()
        self.assertIn("start_date", cm.exception.message_dict)

    def test_project_developer_clean_developer_without_stack(self):
        # Testa se a alocação dispara erro quando o desenvolvedor não possui a stack requerida
        new_stack = Stack.objects.create(
            name="Angular", description="Another framework"
        )
        pd = ProjectDeveloper(
            project=self.project,
            developer=self.developer,
            hours_per_month=40,
            stack=new_stack,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=30),
        )
        with self.assertRaises(ValidationError) as cm:
            pd.clean()
        self.assertIn("stack", cm.exception.message_dict)

    def test_verify_developer_availability_exceeds_hours(self):
        # Cria uma alocação existente que utiliza muitas horas
        ProjectDeveloper.objects.create(
            project=self.project,
            developer=self.developer,
            hours_per_month=140,
            stack=self.stack1,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
        )
        pd = ProjectDeveloper(
            project=self.project,
            developer=self.developer,
            hours_per_month=30,
            stack=self.stack1,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
        )
        available, message = pd.verify_developer_availability()
        self.assertFalse(available)
        self.assertIn("excederá o limite de horas", message)


class ProjectStackModelTest(TestCase):
    def setUp(self):
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.stack1 = Stack.objects.create(name="Vue", description="Frontend framework")
        self.project = Project.objects.create(
            name="Project Stack Test",
            description="Test project",
            tech_leader=self.tech_leader,
            estimated_hours=150,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=35),
            status="PLANNING",
        )

    def test_project_stack_unique_together(self):
        # Cria a primeira associação e tenta criar duplicata
        ProjectStack.objects.create(
            project=self.project, stack=self.stack1, required_developers=2
        )
        with self.assertRaises(Exception):
            ProjectStack.objects.create(
                project=self.project, stack=self.stack1, required_developers=3
            )


class ProjectChangeLogModelTest(TestCase):
    def setUp(self):
        self.tech_leader = User.objects.create_user(
            email="tl@example.com", password="password123", user_type="TL"
        )
        self.project = Project.objects.create(
            name="Project Log Test",
            description="Testing change log",
            tech_leader=self.tech_leader,
            estimated_hours=100,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=20),
            status="PLANNING",
        )
        self.user = self.tech_leader

    def test_project_change_log_str(self):
        log = ProjectChangeLog.objects.create(
            project=self.project,
            action="created",
            user=self.user,
            description="Projeto criado",
        )
        expected_str = (
            f"{self.project.name} - created by {self.user.email} at {log.timestamp}"
        )
        self.assertEqual(str(log), expected_str)
