from django.urls import path
from .views import (
    ProjectViewSet,
    ProjectDeveloperViewSet,
    ProjectStackViewSet,
)

app_name = "projects"

# Mapeamento das ações do ProjectViewSet
project_list_create = ProjectViewSet.as_view({"get": "list", "post": "create"})
project_detail = ProjectViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

# Mapeamento das ações do ProjectDeveloperViewSet (rota aninhada em project_id)
project_developer_list_create = ProjectDeveloperViewSet.as_view(
    {"get": "list", "post": "create"}
)
project_developer_detail = ProjectDeveloperViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

# Mapeamento das ações do ProjectStackViewSet (rota aninhada em project_id)
project_stack_list_create = ProjectStackViewSet.as_view(
    {"get": "list", "post": "create"}
)
project_stack_detail = ProjectStackViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    # Endpoints para Projetos
    path("projects/", project_list_create, name="project-list-create"),
    path("projects/<int:pk>/", project_detail, name="project-detail"),
    # Endpoints para alocações de Desenvolvedores
    path(
        "projects/<int:project_id>/developers/",
        project_developer_list_create,
        name="project-developer-list",
    ),
    path(
        "projects/<int:project_id>/developers/<int:pk>/",
        project_developer_detail,
        name="project-developer-detail",
    ),
    # Endpoints para Stacks do Projeto
    path(
        "projects/<int:project_id>/stacks/",
        project_stack_list_create,
        name="project-stack-list",
    ),
    path(
        "projects/<int:project_id>/stacks/<int:pk>/",
        project_stack_detail,
        name="project-stack-detail",
    ),
]
