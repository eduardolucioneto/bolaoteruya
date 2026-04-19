from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import PoolConfiguration
from worldcup.models import Group, Match, Stage, Stadium, Team


class Command(BaseCommand):
    help = "Popula um ambiente de desenvolvimento com dados iniciais."

    def handle(self, *args, **options):
        config = PoolConfiguration.get_solo()
        config.allow_self_signup = True
        config.save()

        group_a, _ = Group.objects.get_or_create(name="A")
        stage, _ = Stage.objects.get_or_create(order=1, defaults={"name": "Fase de grupos", "stage_type": Stage.GROUPS})
        stadium, _ = Stadium.objects.get_or_create(name="MetLife Stadium", city="New Jersey", country="Estados Unidos")
        home, _ = Team.objects.get_or_create(fifa_code="BRA", defaults={"name": "Brasil", "group": group_a})
        away, _ = Team.objects.get_or_create(fifa_code="ARG", defaults={"name": "Argentina", "group": group_a})
        Match.objects.get_or_create(
            match_number=1,
            defaults={
                "stage": stage,
                "group": group_a,
                "home_team": home,
                "away_team": away,
                "stadium": stadium,
                "start_time": timezone.now() + timedelta(days=2),
            },
        )
        user_model = get_user_model()
        if not user_model.objects.filter(username="admin").exists():
            user_model.objects.create_superuser("admin", "admin@example.com", "admin123456")
        self.stdout.write(self.style.SUCCESS("Ambiente de desenvolvimento populado."))

