from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db import models

from core.exceptions import ProjectValidationError
from core.mixins.audit_mixins import AuditableMixin
from stacks.models import Stack
from users.models import User


# Create your models here.
PROJECT_STATUS = {
    ("PLANNING", "Em Planejamento"),
    ("IN_PROGRESS", "Em Andamento"),
    ("COMPLETED", "Concluído"),
    ("ON_HOLD", "Em Pausa"),
}


class Project(AuditableMixin):
    name = models.CharField(max_length=255, verbose_name="Nome do projeto")
    description = models.TextField(verbose_name="Descrição")
    tech_leader = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="led_projects",
        limit_choices_to={"user_type": "TL"},
        verbose_name="Tech Leader",
    )
    developers = models.ManyToManyField(
        "users.User",
        through="ProjectDeveloper",
        related_name="developer_projects",
        through_fields=("project", "developer"),
        verbose_name="Desenvolvedores",
    )
    stacks = models.ManyToManyField(
        Stack,
        through="ProjectStack",
        related_name="projects",
        verbose_name="Stacks do projeto",
    )
    estimated_hours = models.PositiveBigIntegerField(verbose_name="Horas estimadas")
    start_dat = models.DateField(verbose_name="Data de inicio")
    end_date = models.DateField(verbose_name="Data prevista de termino")
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default="PLANNING")

    def clean(self):
        project_stack = set(self.stacks.all())
        tl_stacks = set(
            self.tech_leader.user_stacks.all().value_list("stack", flat=True)
        )
        missing_stacks = project_stack - tl_stacks
        if missing_stacks:
            raise ProjectValidationError(
                {
                    "tech_leader": "Tech Leader não possui todas as stacks necessárias",
                    "missing_stacks": missing_stacks,
                },
                code="insufficient_tl_stacks",
            )


class ProjectDeveloper(AuditableMixin):
    """
    Modelo intermediário para relacionar desenvolvedores a projetos.
    Inclui informações específicas da alocação do desenvolvedor.
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    developer = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "DEV"}
    )
    stack = models.ForeignKey(
        Stack,
        on_delete=models.CASCADE,
        help_text="Stack que o desenvolvedor utilizará neste projeto",
    )
    hours_per_month = models.PositiveIntegerField(
        verbose_name="Horas por mês",
        help_text="Horas mensais alocadas para esse desenvolvedor",
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def verify_developer_availability(self):
        """
        Verifica se o desenvolvedor tem disponibilidade de horas no período especificado.
        Esta função analisa mês a mês para garantir que não haja sobrecarga em nenhum momento.
        """

        # Busca todas as outras alocações do desenvolvedor que se sobrepõem ao período
        overlapping_allocations = ProjectDeveloper.objects.filter(
            developer=self.developer,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        ).exclude(
            id=self.id
        )  # Exclui a alocação atual em caso de atualização

        # Para cada mês no período, verifica a soma das horas
        current_date = self.start_date
        while current_date <= self.end_date:
            # Calcula o total de horas já alocadas para este mês
            month_allocations = sum(
                allocation.hours_per_month
                for allocation in overlapping_allocations
                if allocation.start_date <= current_date <= allocation.end_date
            )

            # Adiciona as horas desta nova alocação
            total_hours = month_allocations + self.hours_per_month

            # Verifica se excede o limite mensal do desenvolvedor
            if total_hours > self.developer.monthly_hours:
                return False, (
                    f"O desenvolvedor excederá o limite de horas em "
                    f"{current_date.strftime('%B/%Y')}. "
                    f"Total previsto: {total_hours}h, "
                    f"Limite mensal: {self.developer.monthly_hours}h"
                )

            # Avança para o próximo mês
            current_date = (current_date + relativedelta(months=1)).replace(day=1)

        return True, "Dev disponivel"


def clean(self):
    """
    Realiza todas as validações necessárias antes de salvar a alocação.
    Verifica datas, disponibilidade de horas e competências do desenvolvedor.
    """
    from django.core.exceptions import ValidationError

    # Validação básica de datas
    if self.start_date > self.end_date:
        raise ValidationError(
            {"end_date": "A data de término deve ser posterior à data de início"}
        )

    if self.start_date < date.today():
        raise ValidationError(
            {"start_date": "A data de início não pode ser no passado"}
        )

    # Validação de stack do desenvolvedor
    if not self.developer.user_stacks.filter(stack=self.stack).exists():
        raise ValidationError(
            {"stack": f"O desenvolvedor não possui a stack {self.stack.name}"}
        )

    # Verificação de disponibilidade de horas
    is_available, message = self.verify_developer_availability()
    if not is_available:
        raise ValidationError({"hours_per_month": message})

    # Verifica se o projeto ainda precisa de desenvolvedores para esta stack
    project_stack = self.project.projectstack_set.filter(stack=self.stack).first()
    if project_stack:
        current_devs = (
            ProjectDeveloper.objects.filter(project=self.project, stack=self.stack)
            .exclude(id=self.id)
            .count()
        )

        if current_devs >= project_stack.required_developers:
            raise ValidationError(
                {
                    "stack": (
                        f"O projeto já possui o número necessário de "
                        f"desenvolvedores ({project_stack.required_developers}) "
                        f"para a stack {self.stack.name}"
                    )
                }
            )

    super().clean()


def save(self, *args, **kwargs):

    self.clean()
    super().save(*args, **kwargs)


class ProjectStack(models.Model):
    """
    Modelo intermediário para relacionar stacks a projetos.
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE)
    required_developers = models.PositiveIntegerField(
        default=1, help_text="Número de desenvolvedores necessários para esta stack"
    )

    class Meta:
        unique_together = ["project", "stack"]
