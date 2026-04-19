from django.core.management.base import BaseCommand

from predictions.services import lock_expired_predictions


class Command(BaseCommand):
    help = "Trava palpites de partidas já iniciadas."

    def handle(self, *args, **options):
        updated = lock_expired_predictions()
        self.stdout.write(self.style.SUCCESS(f"{updated} palpites travados."))

