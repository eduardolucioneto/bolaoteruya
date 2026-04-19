from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from predictions.models import Prediction
from predictions.services import calculate_prediction_points, lock_expired_predictions, recalculate_match_predictions
from ranking.models import UserScore
from worldcup.models import Group, Match, Stage, Stadium, Team


class PredictionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="bia", email="bia@example.com", password="Senha123456")
        self.group = Group.objects.create(name="A")
        self.stage = Stage.objects.create(name="Fase de grupos", order=1)
        self.stadium = Stadium.objects.create(name="Arena Teste", city="Dallas", country="Estados Unidos")
        self.home = Team.objects.create(name="Brasil", fifa_code="BRA", group=self.group)
        self.away = Team.objects.create(name="Argentina", fifa_code="ARG", group=self.group)

    def test_user_cannot_have_duplicate_prediction(self):
        match = Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=1,
            home_team=self.home,
            away_team=self.away,
            stadium=self.stadium,
            start_time=timezone.now() + timedelta(days=1),
        )
        Prediction.objects.create(user=self.user, match=match, predicted_home_score=2, predicted_away_score=1)
        with self.assertRaises(Exception):
            Prediction.objects.create(user=self.user, match=match, predicted_home_score=1, predicted_away_score=0)

    def test_prediction_is_blocked_after_match_start(self):
        match = Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=2,
            home_team=self.home,
            away_team=self.away,
            stadium=self.stadium,
            start_time=timezone.now() - timedelta(minutes=1),
        )
        prediction = Prediction(user=self.user, match=match, predicted_home_score=1, predicted_away_score=1)
        with self.assertRaises(ValidationError):
            prediction.full_clean()

    def test_points_are_calculated_when_result_exists(self):
        match = Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=3,
            home_team=self.home,
            away_team=self.away,
            stadium=self.stadium,
            start_time=timezone.now() + timedelta(hours=2),
            official_home_score=2,
            official_away_score=1,
            finished=True,
        )
        prediction = Prediction.objects.create(user=self.user, match=match, predicted_home_score=2, predicted_away_score=1)
        self.assertEqual(calculate_prediction_points(prediction), 5)

    def test_recalculate_updates_ranking(self):
        match = Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=4,
            home_team=self.home,
            away_team=self.away,
            stadium=self.stadium,
            start_time=timezone.now() + timedelta(hours=3),
            official_home_score=1,
            official_away_score=0,
            finished=True,
        )
        Prediction.objects.create(user=self.user, match=match, predicted_home_score=1, predicted_away_score=0)
        recalculate_match_predictions(match)
        score = UserScore.objects.get(user=self.user)
        self.assertEqual(score.total_points, 5)
        self.assertEqual(score.position, 1)

    def test_lock_expired_predictions_command_service(self):
        match = Match.objects.create(
            stage=self.stage,
            group=self.group,
            match_number=5,
            home_team=self.home,
            away_team=self.away,
            stadium=self.stadium,
            start_time=timezone.now() + timedelta(hours=1),
        )
        prediction = Prediction.objects.create(user=self.user, match=match, predicted_home_score=0, predicted_away_score=0)
        Match.objects.filter(pk=match.pk).update(start_time=timezone.now() - timedelta(minutes=1))
        updated = lock_expired_predictions()
        prediction.refresh_from_db()
        self.assertEqual(updated, 1)
        self.assertTrue(prediction.locked)

