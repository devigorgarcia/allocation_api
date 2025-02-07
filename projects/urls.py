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
    # Projetos
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    # Desenvolvedores do Projeto
    path(
        "<int:project_id>/developers/",
        ProjectDeveloperListView.as_view(),
        name="project-developer-list",
    ),
    path(
        "<int:project_id>/developers/add/",
        ProjectDeveloperCreateView.as_view(),
        name="project-developer-create",
    ),
    path(
        "<int:project_id>/developers/<int:pk>/",
        ProjectDeveloperDetailView.as_view(),
        name="project-developer-detail",
    ),
    # Stacks do Projeto
    path(
        "<int:project_id>/stacks/",
        ProjectStackListView.as_view(),
        name="project-stack-list",
    ),
    path(
        "<int:project_id>/stacks/add/",
        ProjectStackCreateView.as_view(),
        name="project-stack-create",
    ),
]
