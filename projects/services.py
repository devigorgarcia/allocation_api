from django.db import transaction
from django.core.exceptions import ValidationError
from .models import ProjectDeveloper


class ProjectDeveloperService:
    @staticmethod
    @transaction.atomic
    def create_project_developer(validated_data):
        """
        Cria uma nova alocação de desenvolvedor no projeto.
        Esse método orquestra a criação do objeto, invocando as validações
        implementadas no modelo (via clean/full_clean) e persistindo os dados.
        """
        project_developer = ProjectDeveloper(**validated_data)
        project_developer.full_clean()
        project_developer.save()
        return project_developer

    @staticmethod
    @transaction.atomic
    def update_project_developer(instance, validated_data):
        """
        Atualiza uma instância existente de ProjectDeveloper.
        Esse método aplica os dados validados na instância, invoca as validações
        e persiste as alterações.
        """
        # Atualiza os campos com os dados validados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            # Valida novamente a instância com os novos dados
            instance.full_clean()
        except ValidationError as e:
            raise e

        # Salva as alterações
        instance.save()
        return instance
