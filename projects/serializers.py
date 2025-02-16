from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.db import models
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
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "developer_email",
            "developer_name",
            "stack_name",
            "created_by",
            "updated_by",
        ]

    def validate(self, data):
        """
        Realiza todas as validações necessárias para a alocação de um desenvolvedor.
        """
        data = super().validate(data)

        # Obtém o projeto do contexto ou da instância
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
            # Se for atualização, preserva valores existentes caso não sejam enviados
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
            data.setdefault("end_date", timezone.localdate() + timedelta(days=30))
            data.setdefault("hours_per_month", 0)

        # Cria uma instância temporária (ou usa a instância existente) para chamar o full_clean()
        instance = self.instance if self.instance else ProjectDeveloper(**data)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

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
        Calcula o total de horas alocadas no projeto somando as horas de todos os desenvolvedores.
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
                    # Opcional: recuperar os nomes das stacks faltantes se necessário
                    raise serializers.ValidationError(
                        {
                            "tech_leader": "Tech Leader não possui todas as stacks necessárias"
                        }
                    )

        return data
