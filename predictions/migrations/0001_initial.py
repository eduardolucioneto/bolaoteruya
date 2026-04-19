import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("worldcup", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Prediction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("predicted_home_score", models.PositiveSmallIntegerField()),
                ("predicted_away_score", models.PositiveSmallIntegerField()),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("locked", models.BooleanField(default=False)),
                ("points_awarded", models.PositiveIntegerField(default=0)),
                ("processed", models.BooleanField(default=False)),
                ("match", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="predictions", to="worldcup.match")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="predictions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["match__start_time"], "verbose_name": "palpite", "verbose_name_plural": "palpites"},
        ),
        migrations.AddConstraint(
            model_name="prediction",
            constraint=models.UniqueConstraint(fields=("user", "match"), name="unique_user_match_prediction"),
        ),
        migrations.AddIndex(model_name="prediction", index=models.Index(fields=["user", "submitted_at"], name="prediction_user_id_277ea8_idx")),
        migrations.AddIndex(model_name="prediction", index=models.Index(fields=["match", "processed"], name="prediction_match_i_b6bd73_idx")),
    ]

