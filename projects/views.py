# projects/views.py
from rest_framework import generics, status
from rest_framework.response import Response

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
class ProjectListCreateView(
    ProjectPermissionMixin, ProjectAuditMixin, generics.ListCreateAPIView
):
    """
    View para listar e criar projetos.
    GET: Lista projetos baseado nas permissões do usuário
    POST: Cria um novo projeto (apenas Tech Leaders)
    """

    serializer_class = ProjectSerializer
    permission_classes = [CanViewProject]

    def get_queryset(self):
        user = self.request.user
        # Se for admin, vê todos os projetos
        if user.is_staff:
            return Project.objects.all()
        # Se for Tech Leader, vê seus projetos
        if user.is_tech_leader():
            return Project.objects.filter(tech_leader=user)
        # Se for Dev, vê projetos onde está alocado
        return Project.objects.filter(projectdeveloper__developer=user).distinct()

    def perform_create(self, serializer):
        # Garante que o Tech Leader do projeto é o usuário que está criando
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
    queryset = Project.objects.all()


# Views para Desenvolvedores do Projeto
class ProjectDeveloperCreateView(generics.CreateAPIView):
    """
    View para alocar um desenvolvedor a um projeto.
    POST: Adiciona um desenvolvedor ao projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [IsProjectTechLeader]

    def perform_create(self, serializer):
        # Obtém o projeto do parâmetro da URL
        project_id = self.kwargs.get("project_id")
        project = Project.objects.get(id=project_id)

        # Verifica se o usuário atual é o Tech Leader do projeto
        if project.tech_leader != self.request.user:
            raise ProjectValidationError(
                {"message": "Apenas o Tech Leader pode alocar desenvolvedores"}
            )

        serializer.save(project=project)


class ProjectDeveloperListView(generics.ListAPIView):
    """
    View para listar desenvolvedores de um projeto específico.
    GET: Lista todos os desenvolvedores alocados no projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [CanViewProject]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectDeveloper.objects.filter(project_id=project_id)


class ProjectDeveloperDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para gerenciar a alocação específica de um desenvolvedor.
    GET: Obtém detalhes da alocação
    PUT/PATCH: Atualiza a alocação
    DELETE: Remove o desenvolvedor do projeto
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [IsProjectTechLeader]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectDeveloper.objects.filter(project_id=project_id)


# Views para Stacks do Projeto
class ProjectStackCreateView(generics.CreateAPIView):
    """
    View para adicionar uma stack necessária ao projeto.
    POST: Adiciona uma nova stack ao projeto
    """

    serializer_class = ProjectStackSerializer
    permission_classes = [IsProjectTechLeader]

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = Project.objects.get(id=project_id)
        serializer.save(project=project)


class ProjectStackListView(generics.ListAPIView):
    """
    View para listar as stacks necessárias em um projeto.
    GET: Lista todas as stacks do projeto
    """

    serializer_class = ProjectStackSerializer
    permission_classes = [CanViewProject]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectStack.objects.filter(project_id=project_id)
