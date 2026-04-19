from django.core.management.base import BaseCommand

from worldcup.models import Group, Stage


class Command(BaseCommand):
    help = "Importa grupos e fases padrão da Copa 2026."

    def handle(self, *args, **options):
        for name in "ABCDEFGHIJKL":
            Group.objects.get_or_create(name=name)
        stages = [
            ("Fase de grupos", 1, Stage.GROUPS),
            ("16 avos de final", 2, Stage.ROUND_OF_32),
            ("Oitavas de final", 3, Stage.ROUND_OF_16),
            ("Quartas de final", 4, Stage.QUARTER),
            ("Semifinal", 5, Stage.SEMI),
            ("Terceiro lugar", 6, Stage.THIRD),
            ("Final", 7, Stage.FINAL),
        ]
        for name, order, stage_type in stages:
            Stage.objects.update_or_create(order=order, defaults={"name": name, "stage_type": stage_type})
        self.stdout.write(self.style.SUCCESS("Grupos e fases carregados."))
