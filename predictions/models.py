from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from worldcup.models import Group, Match, Team


class GroupPrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_predictions")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="predictions")
    first_place = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="group_first_predictions", limit_choices_to={"active": True}
    )
    second_place = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="group_second_predictions", limit_choices_to={"active": True}
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "group"], name="unique_user_group_prediction"),
        ]

    def clean(self) -> None:
        if self.first_place_id == self.second_place_id:
            raise ValidationError("1º e 2º colocados devem ser diferentes.")
        if self.group_id != self.first_place.group_id or self.group_id != self.second_place.group_id:
            raise ValidationError("Times devem pertencer ao grupo.")

    def __str__(self) -> str:
        return f"{self.user} - {self.group} ({self.first_place}, {self.second_place})"


class FinalistPrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finalist_predictions")
    position = models.CharField(
        max_length=20,
        choices=[
            ("first", "1º Lugar"),
            ("second", "2º Lugar"),
            ("third", "3º Lugar"),
            ("fourth", "4º Lugar"),
        ],
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, limit_choices_to={"active": True})
    submitted_at = models.DateTimeField(default=timezone.now)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "position"], name="unique_user_position_prediction"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.position}: {self.team}"


class Prediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions")
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="predictions")
    predicted_home_score = models.PositiveSmallIntegerField()
    predicted_away_score = models.PositiveSmallIntegerField()
    submitted_at = models.DateTimeField(default=timezone.now)
    locked = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["match__start_time"]
        verbose_name = "palpite"
        verbose_name_plural = "palpites"
        constraints = [
            models.UniqueConstraint(fields=["user", "match"], name="unique_user_match_prediction"),
        ]
        indexes = [
            models.Index(fields=["user", "submitted_at"]),
            models.Index(fields=["match", "processed"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.match}"

    def clean(self) -> None:
        if self.match_id and self.match.is_locked:
            raise ValidationError("Não é possível palpitar após o início da partida.")
        if self.predicted_home_score is None or self.predicted_away_score is None:
            raise ValidationError("Informe os dois placares.")

    def save(self, *args, **kwargs):
        self.locked = self.match.is_locked
        self.full_clean()
        return super().save(*args, **kwargs)

