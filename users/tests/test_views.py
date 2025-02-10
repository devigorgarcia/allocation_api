from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User


class UserRegistrationViewTest(APITestCase):
    def test_user_registration(self):
        url = reverse("user-register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "user_type": "DEV",
            "password": "newpassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], data["email"])


class UserListViewTest(APITestCase):
    def setUp(self):
        # Cria um Tech Leader e um Developer para testar as regras de permissão
        self.tl_user = User.objects.create_user(
            email="tech@example.com", password="password123", user_type="TL"
        )
        self.dev_user = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        self.url = reverse("user-list")

    def test_tech_leader_can_see_all_users(self):
        self.client.force_authenticate(user=self.tl_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tech Leader deve visualizar todos os usuários (neste exemplo, 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_developer_can_see_only_self(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Developer deve visualizar apenas o próprio perfil
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], self.dev_user.email)


class UserDetailViewTest(APITestCase):
    def setUp(self):
        self.tl_user = User.objects.create_user(
            email="tech@example.com", password="password123", user_type="TL"
        )
        self.dev_user = User.objects.create_user(
            email="dev@example.com", password="password123", user_type="DEV"
        )
        # Função para montar a URL do detalhe com base no pk do usuário
        self.detail_url = lambda pk: reverse("user-detail", kwargs={"pk": pk})

    def test_tech_leader_can_retrieve_any_user_detail(self):
        self.client.force_authenticate(user=self.tl_user)
        response = self.client.get(self.detail_url(self.dev_user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.dev_user.email)

    def test_developer_can_retrieve_own_detail(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(self.detail_url(self.dev_user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.dev_user.email)

    def test_developer_cannot_retrieve_other_user_detail(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(self.detail_url(self.tl_user.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_developer_can_update_own_detail(self):
        """
        Testa se um usuário do tipo 'DEV' pode atualizar seu próprio e-mail.
        """
        self.client.force_authenticate(user=self.dev_user)
        data = {"email": "updated_dev@example.com"}
        response = self.client.patch(
            self.detail_url(self.dev_user.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Atualiza o objeto a partir do banco
        self.dev_user.refresh_from_db()
        self.assertEqual(self.dev_user.email, "updated_dev@example.com")

    def test_developer_cannot_update_other_user_detail(self):
        """
        Testa que um desenvolvedor não pode atualizar os dados de outro usuário.
        """
        self.client.force_authenticate(user=self.dev_user)
        data = {"email": "hacked_tech@example.com"}
        response = self.client.patch(
            self.detail_url(self.tl_user.pk), data, format="json"
        )
        # Deveria ser proibido (403 Forbidden) por causa da permission IsTechLeaderOrSelf
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CustomTokenObtainPairViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="password123", user_type="DEV"
        )
        self.url = reverse("token_obtain_pair")

    def test_token_obtain_pair(self):
        data = {"email": "testuser@example.com", "password": "password123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
