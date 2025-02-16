from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_default_user():
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username="system",
        defaults={
            "email": "system@example.com",
        },
    )
    if created:
        user.set_unusable_password()
        user.save()
    return user


class AuditableMixin(models.Model):
    """
    Mixin que adiciona campos de auditoria aos modelos.

    Este mixin adiciona automaticamente:
    - Quem criou o registro
    - Quando o registro foi criado
    - Quem fez a última modificação
    - Quando foi a última modificação
    """

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_%(class)s_set",
        default=get_default_user,
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="updated_%(class)s_set",
        default=get_default_user,
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        if not self.created_by:
            self.created_by = get_default_user()

        self.updated_by = get_default_user()
        super().save(*args, **kwargs)
