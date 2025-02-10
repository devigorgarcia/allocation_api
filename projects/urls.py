from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ProjectDeveloperCreateView,
    ProjectDeveloperListView,
    ProjectDeveloperDetailView,
    ProjectStackCreateView,
    ProjectStackListView,
)

app_name = "projects"

urlpatterns = [
    # Rotas de Projetos
    path("projects/", ProjectListCreateView.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    # Rotas de Desenvolvedores do Projeto
    path(
        "projects/<int:project_id>/developers/",
        ProjectDeveloperListView.as_view(),
        name="project-developer-list",
    ),
    path(
        "projects/<int:project_id>/developers/add/",
        ProjectDeveloperCreateView.as_view(),
        name="project-developer-create",
    ),
    path(
        "projects/<int:project_id>/developers/<int:pk>/",
        ProjectDeveloperDetailView.as_view(),
        name="project-developer-detail",
    ),  # PK por id da alocação
    path(
        "projects/<int:project_id>/developers/by-developer/<int:developer>/",
        ProjectDeveloperDetailView.as_view(),
        name="project-developer-by-developer",
    ),  # PK por id do dev
    # Rotas de Stacks do Projeto
    path(
        "projects/<int:project_id>/stacks/",
        ProjectStackListView.as_view(),
        name="project-stack-list",
    ),
    path(
        "projects/<int:project_id>/stacks/add/",
        ProjectStackCreateView.as_view(),
        name="project-stack-create",
    ),
]
