from rest_framework import serializers, status
from rest_framework.response import Response
from django.utils import timezone


class ProjectPermissionMixin:
    """
    Mixin que gerencia as permissões relacionadas a projetos.
    Fornece métodos para verificar se um usuário pode realizar
    diferentes ações em um projeto.
    """

    def has_project_permission(self, project, action="view"):
        """
        Verifica se o usuário atual tem permissão para realizar
        uma ação específica no projeto.

        Args:
            project: Instância do projeto a ser verificado
            action: Ação que está sendo tentada ('view', 'edit', 'delete')
        """
        user = self.request.user

        # Admin e Tech Leader do projeto podem fazer tudo
        if user.is_staff or project.tech_leader == user:
            return True

        # Desenvolvedores podem apenas ver projetos em que estão alocados
        if action == "view":
            return project.developers.filter(id=user.id).exists()

        return False


class ProjectAuditMixin:
    """
    Mixin que adiciona funcionalidades de auditoria aos projetos.
    Rastreia criação, modificação e mantém histórico de mudanças.
    """

    def perform_create(self, serializer):
        """
        Customiza o processo de criação para adicionar
        informações de auditoria.
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """
        Customiza o processo de atualização para manter
        o histórico de modificações.
        """
        # Atualiza o registro de quem modificou
        serializer.save(updated_by=self.request.user, updated_at=timezone.now())

        # Registra a modificação no histórico
        self.log_project_change(serializer.instance, "updated", self.request.user)

    def log_project_change(self, project, action, user):
        """
        Registra mudanças significativas no projeto.

        Args:
            project: Projeto que foi modificado
            action: Tipo de ação realizada
            user: Usuário que realizou a ação
        """
        from .models import ProjectChangeLog

        ProjectChangeLog.objects.create(
            project=project,
            action=action,
            user=user,
            description=f"Projeto {action} por {user.email}",
        )


class ProjectValidationMixin:
    """
    Mixin que adiciona validações específicas para projetos.
    Garante que regras de negócio sejam seguidas.
    """

    def validate_project_dates(self, start_date, end_date):
        """
        Valida as datas do projeto para garantir que façam sentido.
        """
        if start_date >= end_date:
            raise serializers.ValidationError(
                {"end_date": "Data final deve ser posterior à data inicial"}
            )

        if start_date < timezone.now().date():
            raise serializers.ValidationError(
                {"start_date": "Data inicial não pode estar no passado"}
            )

    def validate_tech_leader_availability(self, tech_leader, start_date, end_date):
        """
        Verifica se o Tech Leader tem disponibilidade no período.
        """
        overlapping_projects = tech_leader.led_projects.filter(
            start_date__lte=end_date, end_date__gte=start_date
        ).count()

        if overlapping_projects >= 3:  # Limite máximo de projetos simultâneos
            raise serializers.ValidationError(
                {
                    "tech_leader": "Tech Leader já está alocado em muitos projetos neste período"
                }
            )
