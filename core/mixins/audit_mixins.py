from django.db import models
from django.conf import settings


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
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
        verbose_name="Criado por",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
        verbose_name="Atualizado por",
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user

        return super().save(*args, **kwargs)
