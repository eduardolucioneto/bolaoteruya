from django.core.management.base import BaseCommand

from predictions.services import fill_missing_predictions


class Command(BaseCommand):
    help = "Preenche palpites faltantes com placar aleatório 30 minutos antes do jogo."

    def handle(self, *args, **options):
        result = fill_missing_predictions()
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {result['matches_processed']} jogos, criados {result['predictions_created']} palpites automáticos."
            )
        )