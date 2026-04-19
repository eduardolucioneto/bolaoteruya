from django.conf import settings
from django.db import models


class UserScore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="score")
    total_points = models.PositiveIntegerField(default=0)
    stage1_points = models.PositiveIntegerField(default=0)
    stage2_points = models.PositiveIntegerField(default=0)
    exact_hits = models.PositiveIntegerField(default=0)
    outcome_hits = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    stage1_position = models.PositiveIntegerField(default=0)
    stage2_position = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "-total_points", "user__username"]
        verbose_name = "pontuação do usuário"
        verbose_name_plural = "pontuações dos usuários"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.total_points} pts"

