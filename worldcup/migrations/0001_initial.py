import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Group",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=1, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["name"], "verbose_name": "grupo", "verbose_name_plural": "grupos"},
        ),
        migrations.CreateModel(
            name="Stage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("order", models.PositiveSmallIntegerField(unique=True)),
                ("stage_type", models.CharField(choices=[("groups", "Grupos"), ("round_of_32", "16 avos"), ("round_of_16", "Oitavas"), ("quarter", "Quartas"), ("semi", "Semifinal"), ("third", "Terceiro lugar"), ("final", "Final")], default="groups", max_length=20)),
            ],
            options={"ordering": ["order"], "verbose_name": "fase", "verbose_name_plural": "fases"},
        ),
        migrations.CreateModel(
            name="Stadium",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(default="Estados Unidos", max_length=100)),
                ("capacity", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"ordering": ["country", "city", "name"], "verbose_name": "estádio", "verbose_name_plural": "estádios"},
        ),
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("fifa_code", models.CharField(max_length=3, unique=True)),
                ("flag", models.ImageField(blank=True, null=True, upload_to="flags/")),
                ("active", models.BooleanField(default=True)),
                ("group", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teams", to="worldcup.group")),
            ],
            options={"ordering": ["name"], "verbose_name": "seleção", "verbose_name_plural": "seleções"},
        ),
        migrations.CreateModel(
            name="Match",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_number", models.PositiveIntegerField(unique=True)),
                ("start_time", models.DateTimeField()),
                ("status", models.CharField(choices=[("scheduled", "Agendada"), ("live", "Ao vivo"), ("finished", "Encerrada"), ("postponed", "Adiada")], default="scheduled", max_length=20)),
                ("official_home_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("official_away_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("finished", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("away_team", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="away_matches", to="worldcup.team")),
                ("group", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="matches", to="worldcup.group")),
                ("home_team", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="home_matches", to="worldcup.team")),
                ("stadium", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="matches", to="worldcup.stadium")),
                ("stage", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="matches", to="worldcup.stage")),
            ],
            options={"ordering": ["start_time", "match_number"], "verbose_name": "partida", "verbose_name_plural": "partidas"},
        ),
        migrations.AddIndex(model_name="match", index=models.Index(fields=["start_time", "status"], name="worldcup_ma_start_t_5fb9f3_idx")),
        migrations.AddIndex(model_name="match", index=models.Index(fields=["stage", "group"], name="worldcup_ma_stage_i_f2ad2a_idx")),
    ]

