from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PoolConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Bolão Copa do Mundo 2026", max_length=150, verbose_name="nome do bolão")),
                ("year", models.PositiveIntegerField(default=2026)),
                ("active", models.BooleanField(default=True)),
                ("exact_score_points", models.PositiveIntegerField(default=5)),
                ("outcome_points", models.PositiveIntegerField(default=3)),
                ("draw_points", models.PositiveIntegerField(default=3)),
                ("goal_difference_bonus", models.PositiveIntegerField(default=1)),
                ("one_side_goals_bonus", models.PositiveIntegerField(default=1)),
                ("allow_self_signup", models.BooleanField(default=False)),
                ("global_prediction_deadline", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "configuração do bolão", "verbose_name_plural": "configurações do bolão"},
        )
    ]

