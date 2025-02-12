from django.utils import timezone
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db import models
from django.core.exceptions import ValidationError
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
    name = models.CharField(
        max_length=255,
        verbose_name="Nome do projeto",
        help_text="Nome único que identifica o projeto",
    )
    description = models.TextField(
        verbose_name="Descrição",
        help_text="Descrição detalhada do projeto, seus objetivos e escopo",
    )
    tech_leader = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="led_projects",
        limit_choices_to={"user_type": "TL"},
        verbose_name="Tech Leader",
        help_text="Tech Leader responsável pelo projeto. Deve ter as stacks necessárias",
    )
    developers = models.ManyToManyField(
        "users.User",
        through="ProjectDeveloper",
        related_name="developer_projects",
        through_fields=("project", "developer"),
        verbose_name="Desenvolvedores",
        help_text="Desenvolvedores alocados no projeto com suas respectivas stacks e horas",
    )
    stacks = models.ManyToManyField(
        Stack,
        through="ProjectStack",
        related_name="projects",
        verbose_name="Stacks do projeto",
        help_text="Stacks tecnológicas necessárias para o projeto",
    )
    estimated_hours = models.PositiveBigIntegerField(
        verbose_name="Horas estimadas",
        help_text="Total de horas estimadas para a conclusão do projeto",
    )
    start_date = models.DateField(
        verbose_name="Data de Início", help_text="Data planejada para início do projeto"
    )
    end_date = models.DateField(
        verbose_name="Data de Término Previsto",
        help_text="Data prevista para conclusão do projeto",
    )
    status = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS,
        default="PLANNING",
        help_text="Status atual do projeto (Planejamento, Em Andamento, Concluído ou Em Pausa)",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.tech_leader.email}"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": "A data de término deve ser posterior à data de início"}
            )
        project_stack = set(self.stacks.all())
        tl_stacks = set(
            self.tech_leader.user_stacks.all().values_list("stack", flat=True)
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


def default_end_date():
    return timezone.localdate() + timedelta(days=30)


class ProjectDeveloper(AuditableMixin):
    """
    Modelo intermediário para relacionar desenvolvedores a projetos.
    Inclui informações específicas da alocação do desenvolvedor.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        help_text="Projeto ao qual o desenvolvedor está alocado",
    )
    developer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "DEV"},
        help_text="Desenvolvedor alocado no projeto (deve ter o tipo 'DEV')",
    )
    hours_per_month = models.PositiveIntegerField(
        verbose_name="Horas por mês",
        help_text="Quantidade de horas mensais que o desenvolvedor dedicará ao projeto",
        default=0,
    )
    stack = models.ForeignKey(
        Stack,
        on_delete=models.CASCADE,
        null=True,
        help_text="Stack que o desenvolvedor utilizará neste projeto",
    )
    start_date = models.DateField(
        help_text="Data de início da alocação do desenvolvedor no projeto",
        default=timezone.localdate,
    )
    end_date = models.DateField(
        help_text="Data de término prevista para a alocação do desenvolvedor",
        default=default_end_date,
    )

    class Meta:
        ordering = ["start_date"]

    def validate_dates(self):
        """
        Valida se as datas de início e término estão corretas.
        - A data de término deve ser posterior à data de início.
        - Em criação, a data de início não pode estar no passado.
        """
        errors = {}
        if self.start_date > self.end_date:
            errors["end_date"] = "A data de término deve ser posterior à data de início"
        if not self.pk and self.start_date < timezone.localdate():
            errors["start_date"] = "A data de início não pode ser no passado"
        return errors

    def validate_duplicate_allocation(self):
        """
        Valida se o desenvolvedor já não está alocado no mesmo projeto.
        """
        errors = {}
        if self.developer and self.project:
            qs = ProjectDeveloper.objects.filter(
                project=self.project, developer=self.developer
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors["developer"] = "Este desenvolvedor já está alocado neste projeto"
        return errors

    def validate_developer_stacks(self):
        """
        Valida se o desenvolvedor possui a stack que está sendo alocada.
        """
        errors = {}
        if (
            self.stack
            and not self.developer.user_stacks.filter(stack=self.stack).exists()
        ):
            errors["stack"] = f"O desenvolvedor não possui a stack {self.stack.name}"
        return errors

    def validate_stack_capacity(self):
        """
        Valida se o projeto ainda possui vagas para a stack selecionada.
        """
        errors = {}
        # Importação local para evitar import circular
        from projects.models import ProjectStack

        project_stack = ProjectStack.objects.filter(
            project=self.project, stack=self.stack
        ).first()
        if project_stack:
            current_devs = ProjectDeveloper.objects.filter(
                project=self.project, stack=self.stack
            )
            if self.pk:
                current_devs = current_devs.exclude(pk=self.pk)
            if current_devs.count() >= project_stack.required_developers:
                errors["stack"] = (
                    f"O projeto já possui o número necessário de desenvolvedores "
                    f"({project_stack.required_developers}) para a stack {self.stack.name}"
                )
        return errors

    def validate_developer_availability(self):
        errors = {}
        overlapping_allocations = ProjectDeveloper.objects.filter(
            developer=self.developer,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        )
        if self.pk:
            overlapping_allocations = overlapping_allocations.exclude(pk=self.pk)

        current_date = self.start_date
        while current_date <= self.end_date:
            month_allocations = sum(
                allocation.hours_per_month
                for allocation in overlapping_allocations
                if allocation.start_date <= current_date <= allocation.end_date
            )
            total_hours = month_allocations + self.hours_per_month

            if total_hours > self.developer.monthly_hours:
                errors["hours_per_month"] = (
                    f"O desenvolvedor excederá o limite de horas em "
                    f"{current_date.strftime('%B/%Y')}. Total previsto: {total_hours}h, "
                    f"Limite mensal: {self.developer.monthly_hours}h"
                )
                break

            current_date = (current_date + relativedelta(months=1)).replace(day=1)

        return errors

    def clean(self):
        """
        Agrega todas as validações de negócio executando os métodos específicos.
        Se houver algum erro, levanta ValidationError.
        """
        errors = {}
        errors.update(self.validate_dates())
        errors.update(self.validate_duplicate_allocation())
        errors.update(self.validate_developer_stacks())
        errors.update(self.validate_stack_capacity())
        errors.update(self.validate_developer_availability())

        if errors:
            raise ValidationError(errors)

        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ProjectStack(models.Model):
    """
    Modelo intermediário para relacionar stacks a projetos.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        help_text="Projeto ao qual esta stack está associada",
    )
    stack = models.ForeignKey(
        Stack,
        on_delete=models.CASCADE,
        help_text="Stack tecnológica necessária para o projeto",
    )
    required_developers = models.PositiveIntegerField(
        default=1, help_text="Número de desenvolvedores necessários para esta stack"
    )

    class Meta:
        unique_together = ["project", "stack"]
        ordering = ["stack__name"]


class ProjectChangeLog(models.Model):
    """
    Modelo para registrar histórico de mudanças em projetos.
    Mantém um log de todas as alterações significativas.
    """

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="change_logs"
    )
    action = models.CharField(
        max_length=50,
        help_text="Tipo de ação realizada (ex: 'updated', 'created', etc)",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        help_text="Usuário que realizou a ação",
    )
    description = models.TextField(help_text="Descrição detalhada da mudança")
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="Quando a mudança foi realizada"
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.project.name} - {self.action} by {self.user.email} at {self.timestamp}"
