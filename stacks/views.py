from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from stacks.filters import StackFilter, UserStackFilter
from .models import Stack, UserStack
from .serializers import AddUserStackSerializer, StackSerializer, UserStackSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response


class StackListCreateView(generics.ListCreateAPIView):
    queryset = Stack.objects.filter(is_active=True)
    serializer_class = StackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StackFilter

    def get_queryset(self):

        queryset = Stack.objects.filter(is_active=True)
        if not self.request.user.is_tech_leader():
            return queryset.filter(user_stacks__user=self.request.user).distinct()
        return queryset


class UserStackListCreateView(generics.ListCreateAPIView):
    serializer_class = UserStackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserStackFilter

    def get_queryset(self):
        """
        Tech Leaders podem ver todas as associações usuário-stack
        Desenvolvedores veem apenas suas próprias stacks
        """
        if self.request.user.is_tech_leader():
            return UserStack.objects.all().select_related("user", "stack")
        return UserStack.objects.filter(user=self.request.user).select_related(
            "user", "stack"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserStackDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserStackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserStack.objects.filter(user=self.request.user)


class AddUserStackView(generics.CreateAPIView):

    serializer_class = AddUserStackSerializer
    permission_classes = [IsAuthenticated]


class AddUserStackView(generics.CreateAPIView):
    serializer_class = AddUserStackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Determina qual usuário receberá a stack baseado nas permissões e dados da requisição.
        Se for admin/TL, pode escolher o usuário. Se for dev, usa o próprio usuário.
        """
        user = self.request.user

        # Se for admin ou TL, permite escolher o usuário alvo
        if user.is_staff or user.is_tech_leader():
            # Se não especificou usuário, usa o próprio usuário que fez a requisição
            target_user = serializer.validated_data.get("user", user)
        else:
            # Se for dev, ignora qualquer usuário especificado e usa ele mesmo
            target_user = user

        serializer.save(user=target_user)

    def create(self, request, *args, **kwargs):
        """
        Processo de criação com mensagens personalizadas baseadas em quem está
        criando e para quem está sendo criado.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_user = request.user
        target_user = serializer.validated_data.get("user", current_user)

        if current_user == target_user:
            message = "Stack adicionada com sucesso ao seu perfil!"
        else:
            message = f"Stack adicionada com sucesso ao perfil de {target_user.email}!"

        if serializer.validated_data.get("is_primary"):
            message += " (Definida como stack primária)"

        return Response(
            {
                "status": "success",
                "message": message,
                "data": {
                    "stack_info": serializer.data,
                    "assigned_to": target_user.email,
                    "assigned_by": current_user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )
