from django.utils import timezone
from dateutil.relativedelta import relativedelta

from projects.models import Project, ProjectDeveloper
from stacks.models import Stack


class ProjectDeveloperValidator:
    """
    Classe responsável por gerenciar todas as validações relacionadas
    à alocação de desenvolvedores em projetos.
    """

    def __init__(self, project_developer=None, project=None):
        """
        Inicializa o validador garantindo que temos um projeto válido.

        Args:
            project_developer: Instância existente de ProjectDeveloper (opcional)
            project: Instância do projeto para novas alocações
        """
        print(f"Iniciando validação para projeto: {project}")

        self.instance = project_developer

        if project is None and project_developer is not None:
            self.project = project_developer.project
        else:
            self.project = project

        if not self.project:
            raise ValueError("Projeto não encontrado")

        if not isinstance(self.project, Project):
            raise ValueError(f"Tipo inválido para projeto: {type(self.project)}")

        print(f"Validador inicializado com sucesso para o projeto: {self.project.name}")

    def validate_developer_already_allocated(self, developer):
        """
        Verifica se o desenvolvedor já está alocado neste projeto.
        """
        if not developer:
            return False, {"developer": "Desenvolvedor não informado"}

        print(f"Verificando alocação existente para desenvolvedor: {developer}")

        dev_exists = ProjectDeveloper.objects.filter(
            project=self.project, developer=developer
        )

        if self.instance:
            dev_exists = dev_exists.exclude(pk=self.instance.pk)

        if dev_exists.exists():
            print(f"Desenvolvedor já alocado: {developer}")
            return False, {
                "developer": "Este desenvolvedor já está alocado neste projeto"
            }

        print(f"Desenvolvedor disponível para alocação: {developer}")
        return True, None

    def validate_developer_stacks(self, developer):
        """
        Verifica se o desenvolvedor possui as stacks necessárias.
        """

        if not developer:
            return False, {
                "developer": "É necessário fornecer um desenvolvedor para validar as stacks"
            }

        dev_stacks = set(developer.user_stacks.all().values_list("stack", flat=True))
        project_stacks = set(self.project.stacks.all().values_list("id", flat=True))

        if developer.user_type == "TL":
            missing_stacks = project_stacks - dev_stacks
            if missing_stacks:
                stack_names = Stack.objects.filter(id__in=missing_stacks).values_list(
                    "name", flat=True
                )
                return False, {
                    "developer": f"Tech Leader não possui todas as stacks necessárias: {', '.join(stack_names)}"
                }
        else:
            common_stacks = dev_stacks.intersection(project_stacks)
            if not common_stacks:
                return False, {
                    "developer": "Desenvolvedor precisa ter pelo menos uma stack do projeto"
                }

        return True, None

    def validate_dates(self, start_date, end_date):
        if start_date > end_date:
            return False, {
                "end_date": "A data de término deve ser posterior à data de início"
            }

        # Se for criação (não existe self.instance), validar a data de início
        if not self.instance and start_date < timezone.localdate():
            return False, {"start_date": "A data de início não pode ser no passado"}

        return True, None

    def validate_stack_capacity(self, stack):
        """
        Verifica se há vagas disponíveis para a stack.
        """
        project_stack = self.project.projectstack_set.filter(stack=stack).first()
        if project_stack:
            current_devs = ProjectDeveloper.objects.filter(
                project=self.project, stack=stack
            )

            if self.instance and self.instance.pk:
                current_devs = current_devs.exclude(id=self.instance.pk)

            if current_devs.count() >= project_stack.required_developers:
                return False, {
                    "stack": (
                        f"O projeto já possui o número necessário de "
                        f"desenvolvedores ({project_stack.required_developers}) "
                        f"para a stack {stack.name}"
                    )
                }
        return True, None

    def validate_developer_availability(
        self, developer, hours_per_month, start_date, end_date
    ):
        """
        Verifica a disponibilidade de horas do desenvolvedor.
        """
        if not developer:
            return False, {"developer": "Developer is required"}

        if hours_per_month is None:
            hours_per_month = 0

        overlapping_allocations = ProjectDeveloper.objects.filter(
            developer=developer, start_date__lte=end_date, end_date__gte=start_date
        )

        if self.instance and self.instance.pk:
            overlapping_allocations = overlapping_allocations.exclude(
                id=self.instance.pk
            )

        current_date = start_date
        while current_date <= end_date:
            month_allocations = sum(
                allocation.hours_per_month
                for allocation in overlapping_allocations
                if allocation.start_date <= current_date <= allocation.end_date
            )

            total_hours = month_allocations + hours_per_month

            if total_hours > developer.monthly_hours:
                return False, {
                    "hours_per_month": (
                        f"O desenvolvedor excederá o limite de horas em "
                        f"{current_date.strftime('%B/%Y')}. "
                        f"Total previsto: {total_hours}h, "
                        f"Limite mensal: {developer.monthly_hours}h"
                    )
                }

            current_date = (current_date + relativedelta(months=1)).replace(day=1)

        return True, None
