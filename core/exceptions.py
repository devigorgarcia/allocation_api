from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


class ProjectValidationError(DRFValidationError):
    """
    Exceção customizada para erros de validação específicos de projetos.
    Esta classe nos permite diferenciar erros de projeto de outros tipos de erro.
    """

    def __init__(self, detail=None, code=None):

        if code is None:
            code = "project_validation_error"

        if isinstance(detail, str):
            detail = {"error": detail}
        elif isinstance(detail, list):
            detail = {"errors": detail}

        self.metadata = {
            "error_type": "ProjectValidation",
            "error_code": code,
        }

        super().__init__(detail, code)

    def get_full_details(self):
        """
        Retorna detalhes completos do erro, incluindo metadados.
        Útil para logging e debugging.
        """
        return {"detail": self.detail, "code": self.code, "metadata": self.metadata}


class ResourceAllocationError(DRFValidationError):
    """
    Exceção customizada para erros relacionados à alocação de recursos.
    Útil para tratar erros de horas, disponibilidade, etc.
    """

    pass


def format_validation_errors(errors):
    """
    Formata erros de validação de uma maneira consistente e amigável.

    Por exemplo, transforma:
    {'field': ['error1', 'error2']}
    em:
    ['field: error1', 'field: error2']
    """
    if isinstance(errors, dict):
        formatted_errors = []
        for field, error_list in errors.items():
            if isinstance(error_list, (list, tuple)):
                for error in error_list:
                    formatted_errors.append(f"{field}: {error}")
            else:
                formatted_errors.append(f"{field}: {error_list}")
        return formatted_errors
    return [str(errors)]


def custom_exception_handler(exc, context):
    """
    Manipulador global de exceções expandido para tratar casos específicos do projeto.
    """

    response = exception_handler(exc, context)

    if response is None:
        error_data = {
            "status": "error",
            "message": "Ocorreu um erro inesperado",
            "detail": str(exc),
        }

        if isinstance(exc, DjangoValidationError):
            error_data.update(
                {
                    "message": "Erro de validação",
                    "detail": format_validation_errors(exc.message_dict),
                    "code": "django_validation_error",
                }
            )
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    error_responses = {
        401: {
            "status": "error",
            "message": "Autenticação necessária",
            "detail": "Você precisa estar autenticado para acessar esta funcionalidade.",
            "code": "authentication_required",
        },
        403: {
            "status": "error",
            "message": "Permissão negada",
            "detail": "Você não tem permissão para realizar esta ação.",
            "code": "permission_denied",
        },
        404: {
            "status": "error",
            "message": "Não encontrado",
            "detail": "O recurso solicitado não foi encontrado.",
            "code": "not_found",
        },
        400: {
            "status": "error",
            "message": "Requisição inválida",
            "detail": format_validation_errors(
                response.data
                if hasattr(response, "data")
                else "Os dados fornecidos são inválidos."
            ),
            "code": "invalid_request",
        },
    }

    # Tratamento especial para nossas exceções customizadas
    if isinstance(exc, ProjectValidationError):
        response.data = {
            "status": "error",
            "message": "Erro na validação do projeto",
            "detail": format_validation_errors(exc.detail),
            "code": "project_validation_error",
        }
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response

    if isinstance(exc, ResourceAllocationError):
        response.data = {
            "status": "error",
            "message": "Erro na alocação de recursos",
            "detail": format_validation_errors(exc.detail),
            "code": "resource_allocation_error",
        }
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response

    # Aplicamos o mapeamento padrão se não for uma exceção especial
    if response.status_code in error_responses:
        response.data = error_responses[response.status_code]

    return response
