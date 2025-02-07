# core/utils.py
from rest_framework.response import Response
from rest_framework import status


def create_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Cria uma resposta padronizada para a API.
    """
    response_data = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
    }

    if data is not None:
        response_data["data"] = data

    return Response(response_data, status=status_code)
