from projects.models import Project, ProjectDeveloper, ProjectStack
from stacks import serializers
from users.serializers import UserSerializer


class ProjectStackSerializer(serializers.ModelSerializer):
    """
    Serializer para gerenciar as stacks necessárias em um projeto.
    Inclui informações sobre a stack e quantos desenvolvedores são necessários.
    """

    stack_name = serializers.CharField(source="stack.name", red_only=True)

    class Meta:
        model = ProjectStack
        fields = ["id", "stack", "stack_name", "required_developers"]
        read_only_fields = ["stack_name"]


class ProjectDeveloperSerializer(serializers.ModelSerializer):
    """
    Serializer para gerenciar as alocações de desenvolvedores em projetos.
    Inclui informações detalhadas sobre o desenvolvedor e sua função no projeto.
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
            "project",
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


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer principal para projetos, incluindo todas as informações
    """

    tech_leader_detail = UserSerializer(source="tech_leader", read_only=True)
    developers_detail = ProjectDeveloperSerializer(
        source="projectdeveloper_set", many=True, read_only=True
    )
    stacks_detail = ProjectStackSerializer(
        source="projectstack_set", many=True, read_only=True
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "tech_leader",
            "tech_leader_detail",
            "estimated_hours",
            "start_date",
            "end_date",
            "status",
            "developers_detail",
            "stacks_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "tech_leader_detail",
            "developers_detail",
            "stacks_detail",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        tech_leader = data.get("tech_leader")
        if tech_leader and not tech_leader.is_tech_leader():
            raise serializers.ValidationError(
                {"tech_leader": "O usuário selecionado não é um Tech Leader"}
            )
        return data
