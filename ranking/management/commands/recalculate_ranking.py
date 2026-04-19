from django.core.management.base import BaseCommand

from predictions.services import recalculate_user_scores


class Command(BaseCommand):
    help = "Recalcula o ranking geral dos usuários."

    def handle(self, *args, **options):
        recalculate_user_scores()
        self.stdout.write(self.style.SUCCESS("Ranking recalculado."))
