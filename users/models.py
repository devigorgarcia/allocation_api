# users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    USER_TYPES = (("TL", "Tech Leader"), ("DEV", "Developer"))

    email = models.EmailField("email address", unique=True)
    monthly_hours = models.PositiveIntegerField(
        default=160,
        verbose_name="Horas Mensais Disponíveis",
    )
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    user_type = models.CharField(max_length=3, choices=USER_TYPES)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def is_tech_leader(self):
        return self.user_type == "TL"

    def is_developer(self):
        return self.user_type == "DEV"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)
