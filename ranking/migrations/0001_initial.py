import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserScore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_points", models.PositiveIntegerField(default=0)),
                ("exact_hits", models.PositiveIntegerField(default=0)),
                ("outcome_hits", models.PositiveIntegerField(default=0)),
                ("position", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="score", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["position", "-total_points", "user__username"], "verbose_name": "pontuação do usuário", "verbose_name_plural": "pontuações dos usuários"},
        )
    ]

