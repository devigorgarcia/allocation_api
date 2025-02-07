class ProjectPermissionMixin:
    """
    Mixin para gerenciar permissões relacionadas a projetos.
    Define quem pode ver e modificar informações de projetos.
    """

    def has_project_permission(self, project, action="view"):
        user = self.request.user

        # Admin e Tech Leader do projeto podem fazer tudo
        if user.is_staff or project.tech_leader == user:
            return True

        # Desenvolvedores podem apenas ver projetos em que estão alocados
        if action == "view":
            return project.projectdeveloper_set.filter(developer=user).exists()

        return False
