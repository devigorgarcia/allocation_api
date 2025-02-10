from django.http import Http404
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProjectFilter, ProjectDeveloperFilter, ProjectStackFilter
from core.exceptions import ProjectValidationError
from .models import Project, ProjectDeveloper, ProjectStack
from .serializers import (
    ProjectSerializer,
    ProjectDeveloperSerializer,
    ProjectStackSerializer,
)
from .permissions import IsProjectTechLeader, CanViewProject
from .mixins import ProjectPermissionMixin, ProjectAuditMixin


# Views para Projeto
class ProjectListCreateView(ProjectAuditMixin, generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [CanViewProject]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter
    ordering_fields = ["name", "start_date", "end_date", "status"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Project.objects.all()
        if user.is_tech_leader():
            return Project.objects.filter(tech_leader=user)
        return Project.objects.filter(projectdeveloper__developer=user).distinct()

    def perform_create(self, serializer):
        serializer.save(tech_leader=self.request.user)


class ProjectDetailView(
    ProjectPermissionMixin, ProjectAuditMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    View para operações em um projeto específico.
    GET: Obtém detalhes do projeto
    PUT/PATCH: Atualiza o projeto
    DELETE: Remove o projeto
    """

    serializer_class = ProjectSerializer
    permission_classes = [CanViewProject]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectDeveloperFilter
    queryset = Project.objects.all()
    lookup_field = "pk"

    def get_queryset(self):
        return Project.objects.prefetch_related(
            "projectdeveloper_set", "projectstack_set", "tech_leader"
        )


# Views para Desenvolvedores do Projeto
class ProjectDeveloperCreateView(ProjectAuditMixin, generics.CreateAPIView):
    """
    View para alocar um desenvolvedor a um projeto.
    POST: Adiciona um desenvolvedor ao projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [IsProjectTechLeader]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs.get("project_id")

        try:
            project = Project.objects.get(pk=project_id)
            context["project"] = project
        except Project.DoesNotExist:
            raise Http404(f"Projeto com ID {project_id} não encontrado")

        return context

    def perform_create(self, serializer):
        project = Project.objects.get(pk=self.kwargs["project_id"])

        # Verifica se o usuário atual é o Tech Leader do projeto
        if project.tech_leader != self.request.user:
            raise ProjectValidationError(
                {"message": "Apenas o Tech Leader pode alocar desenvolvedores"}
            )

        serializer.save(project=project)


class ProjectDeveloperListView(ProjectAuditMixin, generics.ListAPIView):
    """
    View para listar desenvolvedores de um projeto específico.
    GET: Lista todos os desenvolvedores alocados no projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [CanViewProject]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectStackFilter

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectDeveloper.objects.filter(project_id=project_id)


class ProjectDeveloperDetailView(
    ProjectAuditMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    View para gerenciar a alocação específica de um desenvolvedor.
    GET: Obtém detalhes da alocação
    PUT/PATCH: Atualiza a alocação
    DELETE: Remove o desenvolvedor do projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [IsProjectTechLeader]
    lookup_field = "developer"

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        queryset = ProjectDeveloper.objects.filter(project_id=project_id)

        # um developer_id específico
        if "developer" in self.kwargs:
            queryset = queryset.filter(developer_id=self.kwargs["developer"])

        return queryset.select_related("developer", "stack", "project")

    def get_object(self):
        queryset = self.get_queryset()

        # rota com developer_id
        if "developer" in self.kwargs:
            obj = queryset.first()
            if not obj:
                raise Http404(
                    f"Nenhuma alocação encontrada para o desenvolvedor {self.kwargs['developer']} "
                    f"no projeto {self.kwargs['project_id']}"
                )
            return obj

        # rota com pk
        if "pk" in self.kwargs:
            obj = queryset.filter(pk=self.kwargs["pk"]).first()
            if not obj:
                raise Http404(
                    f"Alocação {self.kwargs['pk']} não encontrada no "
                    f"projeto {self.kwargs['project_id']}"
                )
            return obj

        return super().get_object()

    def perform_destroy(self, instance):
        """
        Customiza o processo de remoção para adicionar log
        """

        instance.delete()


# Views para Stacks do Projeto
class ProjectStackCreateView(ProjectAuditMixin, generics.CreateAPIView):
    """
    View para adicionar uma stack necessária ao projeto.
    POST: Adiciona uma nova stack ao projeto
    """

    serializer_class = ProjectStackSerializer
    permission_classes = [IsProjectTechLeader]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = Project.objects.get(pk=self.kwargs["project_id"])
        return context

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = Project.objects.get(id=project_id)
        serializer.save(project=project)


class ProjectStackListView(ProjectAuditMixin, generics.ListAPIView):
    """
    View para listar as stacks necessárias em um projeto.
    GET: Lista todas as stacks do projeto
    """

    serializer_class = ProjectStackSerializer
    permission_classes = [CanViewProject]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectStack.objects.filter(project_id=project_id)
