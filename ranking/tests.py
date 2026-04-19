from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from predictions.models import Prediction
from predictions.services import recalculate_match_predictions
from ranking.models import UserScore
from worldcup.models import Group, Match, Stage, Stadium, Team


class RankingTests(TestCase):
    def test_ranking_orders_by_points_and_exact_hits(self):
        user_model = get_user_model()
        user1 = user_model.objects.create_user(username="u1", email="u1@example.com", password="Senha123456")
        user2 = user_model.objects.create_user(username="u2", email="u2@example.com", password="Senha123456")
        group = Group.objects.create(name="C")
        stage = Stage.objects.create(name="Fase de grupos", order=1)
        stadium = Stadium.objects.create(name="Arena 2", city="Boston", country="Estados Unidos")
        home = Team.objects.create(name="França", fifa_code="FRA", group=group)
        away = Team.objects.create(name="Alemanha", fifa_code="GER", group=group)
        match = Match.objects.create(
            stage=stage,
            group=group,
            match_number=20,
            home_team=home,
            away_team=away,
            stadium=stadium,
            start_time=timezone.now() + timedelta(hours=5),
            official_home_score=2,
            official_away_score=1,
            finished=True,
        )
        Prediction.objects.create(user=user1, match=match, predicted_home_score=2, predicted_away_score=1)
        Prediction.objects.create(user=user2, match=match, predicted_home_score=1, predicted_away_score=0)
        recalculate_match_predictions(match)
        ranking = list(UserScore.objects.order_by("position"))
        self.assertEqual(ranking[0].user, user1)
        self.assertGreater(ranking[0].total_points, ranking[1].total_points)


class RankingAdminExportTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Senha123456",
        )
        self.player = user_model.objects.create_user(
            username="jogador1",
            email="jogador1@example.com",
            password="Senha123456",
        )
        UserScore.objects.create(
            user=self.player,
            total_points=12,
            exact_hits=3,
            outcome_hits=4,
            position=1,
        )
        self.client.force_login(self.admin_user)

    def test_ranking_admin_export_returns_csv(self):
        response = self.client.get(reverse("admin:ranking_userscore_export_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn('filename="ranking.csv"', response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("posicao,usuario,email,pontos,acertos_exatos,acertos_resultado,atualizado_em", content)
        self.assertIn("1,jogador1,jogador1@example.com,12,3,4", content)
