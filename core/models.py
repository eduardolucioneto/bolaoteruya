from django.db import models
from django.conf import settings


class PrizeStage(models.TextChoices):
    STAGE_1 = "stage_1", "1ª Fase (Grupos)"
    STAGE_2 = "stage_2", "2ª Fase (Mata-mata)"
    FINAL = "final", "Final"


class PoolConfiguration(models.Model):
    name = models.CharField("nome do bolão", max_length=150, default="Bolão Copa do Mundo 2026")
    year = models.PositiveIntegerField(default=2026)
    active = models.BooleanField(default=True)
    exact_score_points = models.PositiveIntegerField(default=5)
    outcome_points = models.PositiveIntegerField(default=3)
    draw_points = models.PositiveIntegerField(default=3)
    goal_difference_bonus = models.PositiveIntegerField(default=1)
    one_side_goals_bonus = models.PositiveIntegerField(default=1)
    quota_price = models.PositiveIntegerField("valor da cota", default=30)
    stage1_first_percent = models.PositiveIntegerField("1º lugar 1ª fase %", default=13)
    stage1_second_percent = models.PositiveIntegerField("2º lugar 1ª fase %", default=10)
    stage1_third_percent = models.PositiveIntegerField("3º lugar 1ª fase %", default=7)
    stage2_first_percent = models.PositiveIntegerField("1º lugar 2ª fase %", default=34)
    stage2_second_percent = models.PositiveIntegerField("2º lugar 2ª fase %", default=23)
    stage2_third_percent = models.PositiveIntegerField("3º lugar 2ª fase %", default=13)
    extra_prize_threshold = models.PositiveIntegerField("limite participantes prêmio extra", default=20)
    extra_prize_per_participants = models.PositiveIntegerField("prêmios extras a cada X participantes", default=2)
    extra_prize_value = models.PositiveIntegerField("valor prêmio extra", default=30)
    allow_self_signup = models.BooleanField(default=False)
    signup_whatsapp_number = models.CharField(
        "WhatsApp para cadastro",
        max_length=20,
        default="43984928377",
        help_text="Número no formato internacional ou apenas dígitos. Ex.: 5543999999999",
    )
    global_prediction_deadline = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuração do bolão"
        verbose_name_plural = "configurações do bolão"

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"

    @property
    def signup_whatsapp_link(self) -> str:
        digits = "".join(char for char in self.signup_whatsapp_number if char.isdigit())
        return f"https://wa.me/{digits}" if digits else "#"

    @classmethod
    def get_solo(cls) -> "PoolConfiguration":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def calculate_prizes(self, participant_count: int) -> dict:
        total_collected = participant_count * self.quota_price
        extra_prizes = max(0, participant_count - self.extra_prize_threshold)
        extra_prize_count = (extra_prizes // self.extra_prize_per_participants) + (1 if extra_prizes % self.extra_prize_per_participants > 0 else 0)
        extra_total = extra_prize_count * self.extra_prize_value
        prize_pool = total_collected - extra_total

        stage1_pool = prize_pool * 30 // 100
        stage2_pool = prize_pool * 70 // 100

        stage1_first = int(stage1_pool * self.stage1_first_percent / 100)
        stage1_second = int(stage1_pool * self.stage1_second_percent / 100)
        stage1_third = int(stage1_pool * self.stage1_third_percent / 100)

        stage2_first = int(stage2_pool * self.stage2_first_percent / 100)
        stage2_second = int(stage2_pool * self.stage2_second_percent / 100)
        stage2_third = int(stage2_pool * self.stage2_third_percent / 100)

        remainder = total_collected - (extra_total + stage1_first + stage1_second + stage1_third + stage2_first + stage2_second + stage2_third)
        stage2_first += remainder

        return {
            "total_collected": total_collected,
            "prize_pool": prize_pool,
            "extra_prize_count": extra_prize_count,
            "extra_prize_value": self.extra_prize_value,
            "stage1": {"first": stage1_first, "second": stage1_second, "third": stage1_third},
            "stage2": {"first": stage2_first, "second": stage2_second, "third": stage2_third},
        }
