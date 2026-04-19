from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from worldcup.models import Group, Match, Stage, Stadium, Team


class WorldCupModelTests(TestCase):
    def test_match_cannot_repeat_same_team(self):
        group = Group.objects.create(name="B")
        stage = Stage.objects.create(name="Fase de grupos", order=1)
        stadium = Stadium.objects.create(name="Arena", city="Miami", country="Estados Unidos")
        team = Team.objects.create(name="Brasil", fifa_code="BRA", group=group)
        match = Match(
            stage=stage,
            group=group,
            match_number=10,
            home_team=team,
            away_team=team,
            stadium=stadium,
            start_time=timezone.now() + timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            match.full_clean()


class WorldCupAdminExportTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Senha123456",
        )
        self.client.force_login(self.admin_user)

        self.group = Group.objects.create(name="A", description="Grupo principal")
        self.stage = Stage.objects.create(name="Fase de grupos", order=1)
        self.stadium = Stadium.objects.create(name="MetLife", city="New Jersey", country="Estados Unidos")
        self.team_one = Team.objects.create(name="Brasil", fifa_code="BRA", group=self.group)
        self.team_two = Team.objects.create(name="Argentina", fifa_code="ARG", group=self.group)
        Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=1,
            home_team=self.team_one,
            away_team=self.team_two,
            stadium=self.stadium,
            start_time=timezone.now() + timedelta(days=1),
        )

    def test_group_admin_export_returns_csv(self):
        response = self.client.get(reverse("admin:worldcup_group_export_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn('filename="grupos.csv"', response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("grupo,descricao,selecoes", content)
        self.assertIn("A,Grupo principal,2", content)

    def test_match_admin_export_returns_csv(self):
        response = self.client.get(reverse("admin:worldcup_match_export_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn('filename="jogos.csv"', response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("numero,fase,grupo,mandante,visitante,estadio,inicio,status,placar", content)
        self.assertIn("Brasil", content)
        self.assertIn("Argentina", content)

    def test_team_admin_export_returns_csv(self):
        response = self.client.get(reverse("admin:worldcup_team_export_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn('filename="tabela.csv"', response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("selecao,codigo_fifa,grupo,ativa", content)
        self.assertIn("Brasil,BRA,A,Sim", content)
