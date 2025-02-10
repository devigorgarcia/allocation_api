# from django.test import TestCase
# from datetime import date, timedelta
# from projects.models import Project, ProjectDeveloper
# from projects.validators import ProjectDeveloperValidator
# from users.models import User
# from stacks.models import Stack


# class ProjectDeveloperValidatorTest(TestCase):
#     def setUp(self):
#         self.tech_leader = User.objects.create_user(
#             email="tl@example.com", password="password123", user_type="TL"
#         )
#         self.developer = User.objects.create_user(
#             email="dev@example.com",
#             password="password123",
#             user_type="DEV",
#             monthly_hours=160,
#         )
#         self.stack1 = Stack.objects.create(
#             name="Node.js", description="Backend framework"
#         )
#         self.developer.user_stacks.create(
#             stack=self.stack1,
#             proficiency_level="INT",
#             years_of_experience=2,
#             is_primary=True,
#         )
#         self.project = Project.objects.create(
#             name="Validator Test Project",
#             description="Testing validators",
#             tech_leader=self.tech_leader,
#             estimated_hours=200,
#             start_date=date.today() + timedelta(days=10),
#             end_date=date.today() + timedelta(days=40),
#             status="PLANNING",
#         )
#         self.project.stacks.add(self.stack1)

#     def test_validate_developer_already_allocated(self):
#         # Cria uma alocação já existente
#         pd = ProjectDeveloper.objects.create(
#             project=self.project,
#             developer=self.developer,
#             hours_per_month=50,
#             stack=self.stack1,
#             start_date=date.today() + timedelta(days=10),
#             end_date=date.today() + timedelta(days=40),
#         )
#         validator = ProjectDeveloperValidator(
#             project_developer=pd, project=self.project
#         )
#         valid, error = validator.validate_developer_already_allocated(self.developer)
#         self.assertFalse(valid)
#         self.assertIn("já está alocado", error.get("developer", ""))

#     def test_validate_dates_invalid(self):
#         validator = ProjectDeveloperValidator(project=self.project)
#         valid, error = validator.validate_dates(
#             date.today() + timedelta(days=50), date.today() + timedelta(days=40)
#         )
#         self.assertFalse(valid)
#         self.assertIn("A data de término", error.get("end_date", ""))

#     def test_validate_stack_capacity(self):
#         # Cria um ProjectStack com capacidade 1
#         from projects.models import ProjectStack

#         ps = ProjectStack.objects.create(
#             project=self.project, stack=self.stack1, required_developers=1
#         )
#         # Cria uma alocação e tenta adicionar outra para a mesma stack
#         ProjectDeveloper.objects.create(
#             project=self.project,
#             developer=self.developer,
#             hours_per_month=40,
#             stack=self.stack1,
#             start_date=date.today() + timedelta(days=10),
#             end_date=date.today() + timedelta(days=40),
#         )
#         validator = ProjectDeveloperValidator(project=self.project)
#         valid, error = validator.validate_stack_capacity(self.stack1)
#         self.assertFalse(valid)
#         self.assertIn("já possui o número necessário", error.get("stack", ""))
