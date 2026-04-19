from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from worldcup.models import Group, Match, Stage, Stadium, Team


class Command(BaseCommand):
    help = "Popula partidas iniciais para desenvolvimento."

    def handle(self, *args, **options):
        stage = Stage.objects.filter(order=1).first()
        group = Group.objects.filter(name="A").first()
        teams = list(Team.objects.filter(group=group).order_by("name")[:2])
        stadium, _ = Stadium.objects.get_or_create(name="SoFi Stadium", city="Los Angeles", country="Estados Unidos")
        if not stage or not group or len(teams) < 2:
            raise CommandError("Cadastre fase, grupo A e ao menos duas seleções no grupo A antes de rodar este comando.")
        Match.objects.get_or_create(
            match_number=100,
            defaults={
                "stage": stage,
                "group": group,
                "home_team": teams[0],
                "away_team": teams[1],
                "stadium": stadium,
                "start_time": timezone.now() + timedelta(days=3),
            },
        )
        self.stdout.write(self.style.SUCCESS("Partidas iniciais populadas."))

