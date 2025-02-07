from django.db import models

from core.mixins.audit_mixins import AuditableMixin


class Stack(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Stack"
        verbose_name_plural = "Stacks"

    def __str__(self):
        return self.name


class UserStack(AuditableMixin):
    PROFICIENCY_LEVELS = (
        ("BEG", "Beginner"),
        ("INT", "Intermediate"),
        ("ADV", "Advanced"),
        ("EXP", "Expert"),
    )

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="user_stacks"
    )
    stack = models.ForeignKey(
        Stack, on_delete=models.CASCADE, related_name="user_stacks"
    )
    proficiency_level = models.CharField(max_length=3, choices=PROFICIENCY_LEVELS)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "stack")
        ordering = ["-is_primary", "stack__name"]

    def __str__(self):
        return f"{self.user.email} - {self.stack.name} ({self.get_proficiency_level_display()})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            UserStack.objects.filter(user=self.user, is_primary=True).update(
                is_primary=False
            )
        super().save(*args, **kwargs)
