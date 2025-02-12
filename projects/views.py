from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
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
from .services import (
    ProjectDeveloperService,
)  # Service para criação/atualização de ProjectDeveloper


# ViewSet para Projetos
class ProjectViewSet(ProjectAuditMixin, viewsets.ModelViewSet):
    """
    Gerencia operações (list, retrieve, create, update, destroy) para Projetos.
    O queryset é filtrado conforme o usuário (staff, tech leader ou desenvolvedor alocado).
    """

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


# ViewSet para Alocações de Desenvolvedores em Projetos
class ProjectDeveloperViewSet(ProjectAuditMixin, viewsets.ModelViewSet):
    """
    Gerencia as alocações de desenvolvedores em um projeto específico.
    As operações (create, update, retrieve, destroy) usam o service para
    orquestrar a criação e atualização, garantindo que as validações do modelo
    sejam executadas.
    """

    serializer_class = ProjectDeveloperSerializer
    permission_classes = [IsProjectTechLeader]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectDeveloperFilter

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectDeveloper.objects.filter(project_id=project_id).select_related(
            "developer", "stack", "project"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        context["project"] = project
        return context

    def create(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        if project.tech_leader != request.user:
            raise ProjectValidationError(
                {"message": "Apenas o Tech Leader pode alocar desenvolvedores"}
            )

        serializer = self.get_serializer(
            data=request.data, context={"project": project}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        # INJEÇÃO dos campos de auditoria:
        validated_data["created_by"] = request.user
        validated_data["updated_by"] = request.user

        instance = ProjectDeveloperService.create_project_developer(validated_data)
        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"project": project}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        # Atualiza o campo updated_by com o usuário logado:
        validated_data["updated_by"] = request.user

        updated_instance = ProjectDeveloperService.update_project_developer(
            instance, validated_data
        )
        output_serializer = self.get_serializer(updated_instance)
        return Response(output_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ViewSet para Stacks Necessárias no Projeto
class ProjectStackViewSet(ProjectAuditMixin, viewsets.ModelViewSet):
    """
    Gerencia as stacks necessárias de um projeto.
    Apenas o Tech Leader (ou quem tiver a permissão adequada) pode criar/atualizar.
    """

    serializer_class = ProjectStackSerializer
    permission_classes = [IsProjectTechLeader]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectStackFilter

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectStack.objects.filter(project_id=project_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        context["project"] = project
        return context

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        serializer.save(project=project)
