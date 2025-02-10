from datetime import timedelta
from django.utils import timezone
from django.db import models
from rest_framework import serializers
from projects.validators import ProjectDeveloperValidator
from users.serializers import UserSerializer
from .models import Project, ProjectDeveloper, ProjectStack


class ProjectStackSerializer(serializers.ModelSerializer):
    """
    Serializer para gerenciar as stacks necessárias em um projeto.
    Fornece informações sobre a stack e a quantidade de desenvolvedores necessários.
    """

    stack_name = serializers.CharField(source="stack.name", read_only=True)

    class Meta:
        model = ProjectStack
        fields = ["id", "stack", "stack_name", "required_developers"]
        read_only_fields = ["stack_name"]

    def validate(self, data):
        project = self.context.get("project")
        if not project:
            raise serializers.ValidationError(
                {"project": "Project must be specified in serializer context"}
            )

        data["project"] = project
        if not project.tech_leader.user_stacks.filter(stack=data.get("stack")).exists():
            raise serializers.ValidationError(
                {
                    "stack": "Tech Leader não possui a stack necessária para este projeto."
                }
            )
        return data


class ProjectDeveloperSerializer(serializers.ModelSerializer):
    """
    Serializer para gerenciar as alocações de desenvolvedores em projetos.
    Inclui detalhes do desenvolvedor, stack utilizada e informações de alocação.
    """

    developer_email = serializers.CharField(source="developer.email", read_only=True)
    developer_name = serializers.CharField(
        source="developer.get_full_name", read_only=True
    )
    stack_name = serializers.CharField(source="stack.name", read_only=True)

    class Meta:
        model = ProjectDeveloper
        fields = [
            "id",
            "developer",
            "developer_email",
            "developer_name",
            "stack",
            "stack_name",
            "hours_per_month",
            "start_date",
            "end_date",
        ]
        read_only_fields = ["developer_email", "developer_name", "stack_name"]

    def validate(self, data):
        """
        Realiza todas as validações necessárias para a alocação de um desenvolvedor.
        """
        data = super().validate(data)

        project = self.context.get("project") or (
            self.instance and self.instance.project
        )

        if not project:
            raise serializers.ValidationError(
                {
                    "project": "Erro interno: Projeto não encontrado no contexto do serializer"
                }
            )

        data["project"] = project

        if self.instance:
            data["developer"] = data.get("developer", self.instance.developer)
            data["stack"] = data.get("stack", self.instance.stack)
            data["start_date"] = data.get("start_date", self.instance.start_date)
            data["end_date"] = data.get("end_date", self.instance.end_date)
            data["hours_per_month"] = data.get(
                "hours_per_month", self.instance.hours_per_month
            )
        else:
            # Se for criação, define valores default para os campos ausentes
            data.setdefault("start_date", timezone.localdate())
            from datetime import timedelta

            data.setdefault("end_date", timezone.localdate() + timedelta(days=30))
            data.setdefault("hours_per_month", 0)

        try:
            validator = ProjectDeveloperValidator(self.instance, project)

            validations = [
                validator.validate_developer_already_allocated(data.get("developer")),
                validator.validate_developer_stacks(data.get("developer")),
                validator.validate_dates(data.get("start_date"), data.get("end_date")),
                validator.validate_stack_capacity(data.get("stack")),
            ]

            # Verifica os resultados das validações
            for is_valid, error in validations:
                if not is_valid:
                    raise serializers.ValidationError(error)

            # Validação de disponibilidade
            is_available, error = validator.validate_developer_availability(
                data.get("developer"),
                data.get("hours_per_month"),
                data.get("start_date"),
                data.get("end_date"),
            )
            if not is_available:
                raise serializers.ValidationError(error)

        except ValueError as e:
            # Melhora a mensagem de erro para ser mais específica
            raise serializers.ValidationError({"error": f"Erro de validação: {str(e)}"})

        return data


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer principal para projetos.
    Inclui informações detalhadas sobre o projeto, tech leader,
    desenvolvedores alocados e stacks necessárias.
    """

    tech_leader_detail = UserSerializer(source="tech_leader", read_only=True)
    developers = ProjectDeveloperSerializer(
        source="projectdeveloper_set", many=True, read_only=True
    )
    stacks = ProjectStackSerializer(
        source="projectstack_set", many=True, read_only=True
    )
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "tech_leader",
            "tech_leader_detail",
            "developers",
            "stacks",
            "estimated_hours",
            "total_hours",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "tech_leader_detail",
            "developers",
            "stacks",
            "total_hours",
            "created_at",
            "updated_at",
        ]

    def get_total_hours(self, obj):
        """
        Calcula o total de horas alocadas no projeto
        somando as horas de todos os desenvolvedores.
        """
        return (
            obj.projectdeveloper_set.aggregate(total=models.Sum("hours_per_month"))[
                "total"
            ]
            or 0
        )

    def validate(self, data):
        """
        Realiza validações específicas do projeto:
        - Verifica se as datas são válidas
        - Verifica se o tech leader tem as permissões necessárias
        """
        data = super().validate(data)

        # Validação de datas
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] > data["end_date"]:
                raise serializers.ValidationError(
                    {
                        "end_date": "A data de término deve ser posterior à data de início"
                    }
                )

        tech_leader = data.get("tech_leader")

        if tech_leader is None and self.instance:
            tech_leader = self.instance.tech_leader

        if tech_leader:

            if not tech_leader.is_tech_leader():
                raise serializers.ValidationError(
                    {"tech_leader": "O usuário selecionado não é um Tech Leader"}
                )

            # Valida as stacks apenas se temos uma instância (atualização)
            if self.instance:
                project_stacks = set(self.instance.stacks.values_list("id", flat=True))
                tl_stacks = set(
                    tech_leader.user_stacks.all().values_list("stack", flat=True)
                )

                missing_stacks = project_stacks - tl_stacks
                if missing_stacks:
                    stack_names = [stack.name for stack in missing_stacks]
                    raise serializers.ValidationError(
                        {
                            "tech_leader": f"Tech Leader não possui todas as stacks necessárias: {', '.join(stack_names)}"
                        }
                    )

        return data
