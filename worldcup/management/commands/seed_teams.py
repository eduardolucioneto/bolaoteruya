from django.core.management.base import BaseCommand

from worldcup.models import Team


class Command(BaseCommand):
    help = "Cria algumas seleções iniciais para desenvolvimento."

    def handle(self, *args, **options):
        teams = [
            ("Brasil", "BRA"),
            ("Argentina", "ARG"),
            ("França", "FRA"),
            ("Alemanha", "GER"),
            ("Espanha", "ESP"),
            ("Portugal", "POR"),
            ("Estados Unidos", "USA"),
            ("México", "MEX"),
        ]
        for name, fifa_code in teams:
            Team.objects.get_or_create(fifa_code=fifa_code, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS("Seleções iniciais criadas."))

