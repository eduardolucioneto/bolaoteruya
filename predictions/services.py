from django.db import models, transaction
from django.db.models import Count, Sum
from django.utils import timezone

from core.models import PoolConfiguration
from predictions.models import FinalistPrediction, GroupPrediction, Prediction
from ranking.models import UserScore
from worldcup.models import Group, Match, Stage, Team


def _match_outcome(home: int, away: int) -> str:
    if home > away:
        return "home"
    if away > home:
        return "away"
    return "draw"


def _get_stage_multiplier(stage_type: str) -> tuple[int, int]:
    if stage_type == Stage.GROUPS:
        return 1, 1
    if stage_type == Stage.ROUND_OF_32:
        return 1, 1
    if stage_type == Stage.ROUND_OF_16:
        return 2, 2
    if stage_type in (Stage.QUARTER, Stage.SEMI, Stage.FINAL):
        return 4, 4
    return 1, 1


def calculate_prediction_points(prediction: Prediction, config: PoolConfiguration | None = None) -> int:
    config = config or PoolConfiguration.get_solo()
    match = prediction.match
    if match.official_home_score is None or match.official_away_score is None:
        return 0

    if (
        prediction.predicted_home_score == match.official_home_score
        and prediction.predicted_away_score == match.official_away_score
    ):
        stage = match.stage
        if stage.stage_type == Stage.GROUPS:
            return 3
        result_mult, goals_mult = _get_stage_multiplier(stage.stage_type)
        return result_mult * 3 + goals_mult * 2

    points = 0
    official_outcome = _match_outcome(match.official_home_score, match.official_away_score)
    predicted_outcome = _match_outcome(prediction.predicted_home_score, prediction.predicted_away_score)

    result_mult, goals_mult = _get_stage_multiplier(match.stage.stage_type)

    if official_outcome == predicted_outcome:
        points += result_mult

    if official_outcome == "draw" and predicted_outcome == "draw":
        points += result_mult
    elif official_outcome == predicted_outcome:
        if prediction.predicted_home_score == match.official_home_score:
            points += goals_mult
        if prediction.predicted_away_score == match.official_away_score:
            points += goals_mult

    return points


def calculate_group_prediction_points(prediction: GroupPrediction) -> int:
    team1 = prediction.first_place
    team2 = prediction.second_place
    points = 0
    first_correct = team1 in team1.group.teams.filter(position=1)
    second_correct = team2 in team1.group.teams.filter(position=2)
    if first_correct:
        points += 7
    if second_correct:
        points += 5
    if team1 in team1.group.teams.filter(position__lte=2):
        points += 5
    if team2 in team1.group.teams.filter(position__lte=2):
        points += 5
    return points


def calculate_finalist_prediction_points(prediction: FinalistPrediction, stage1_preds: list[FinalistPrediction], stage1_teams: dict) -> int:
    position = prediction.position
    team = prediction.team
    team_id = team.id
    points = 0
    if position == "first":
        points = 12 if team_id == stage1_teams.get("first") else (8 if team_id in [stage1_teams.get(k) for k in ["first", "second", "third", "fourth"]] else 0)
    elif position == "second":
        points = 8 if team_id == stage1_teams.get("second") else (5 if team_id in [stage1_teams.get(k) for k in ["first", "second", "third", "fourth"]] else 0)
    elif position == "third":
        points = 5 if team_id == stage1_teams.get("third") else (3 if team_id in [stage1_teams.get(k) for k in ["first", "second", "third", "fourth"]] else 0)
    elif position == "fourth":
        points = 3 if team_id == stage1_teams.get("fourth") else 0
    return points


@transaction.atomic
def recalculate_match_predictions(match: Match) -> None:
    predictions = Prediction.objects.select_related("user", "match").filter(match=match)
    for prediction in predictions:
        Prediction.objects.filter(pk=prediction.pk).update(
            points_awarded=calculate_prediction_points(prediction),
            processed=match.finished,
            locked=match.is_locked,
        )
    recalculate_user_scores()


@transaction.atomic
def recalculate_user_scores() -> None:
    config = PoolConfiguration.get_solo()

    stage1_matches = Match.objects.filter(stage__stage_type=Stage.GROUPS, finished=True)
    stage1_match_ids = set(stage1_matches.values_list("id", flat=True))

    aggregates = (
        Prediction.objects.select_related("user", "match")
        .values("user")
        .annotate(
            total_points=Sum("points_awarded"),
            exact_hits=Count(
                "id",
                filter=models.Q(predicted_home_score=models.F("match__official_home_score"))
                & models.Q(predicted_away_score=models.F("match__official_away_score")),
            ),
            outcome_hits=Count("id", filter=models.Q(points_awarded__gte=1)),
        )
    )

    stage1_aggregates = (
        Prediction.objects.select_related("user", "match")
        .filter(match_id__in=stage1_match_ids)
        .values("user")
        .annotate(stage1_points=Sum("points_awarded"))
    )

    stage2_aggregates = (
        Prediction.objects.select_related("user", "match")
        .exclude(match_id__in=stage1_match_ids)
        .filter(match__finished=True)
        .values("user")
        .annotate(stage2_points=Sum("points_awarded"))
    )

    stage1_points_map = {item["user"]: item["stage1_points"] or 0 for item in stage1_aggregates}
    stage2_points_map = {item["user"]: item["stage2_points"] or 0 for item in stage2_aggregates}

    group_preds = GroupPrediction.objects.select_related("first_place", "second_place", "group")
    for gp in group_preds:
        points = calculate_group_prediction_points(gp)
        gp.points_awarded = points
        gp.save(update_fields=["points_awarded"])
        user_id = gp.user_id
        stage1_points_map[user_id] = stage1_points_map.get(user_id, 0) + points

    UserScore.objects.all().delete()
    rows = []
    for item in aggregates:
        user_id = item["user"]
        stage1 = stage1_points_map.get(user_id, 0)
        stage2 = stage2_points_map.get(user_id, 0)
        rows.append(
            UserScore(
                user_id=user_id,
                total_points=item["total_points"] or 0,
                stage1_points=stage1,
                stage2_points=stage2,
                exact_hits=item["exact_hits"] or 0,
                outcome_hits=item["outcome_hits"] or 0,
            )
        )
    UserScore.objects.bulk_create(rows)

    for position, score in enumerate(UserScore.objects.select_related("user").order_by("-total_points", "-exact_hits", "-outcome_hits", "user__username"), start=1):
        score.position = position
        score.save(update_fields=["position"])

    for position, score in enumerate(UserScore.objects.select_related("user").order_by("-stage1_points", "-exact_hits", "user__username"), start=1):
        score.stage1_position = position
        score.save(update_fields=["stage1_position"])

    for position, score in enumerate(UserScore.objects.select_related("user").order_by("-stage2_points", "-exact_hits", "user__username"), start=1):
        score.stage2_position = position
        score.save(update_fields=["stage2_position"])


def lock_expired_predictions() -> int:
    updated = Prediction.objects.filter(locked=False, match__start_time__lte=timezone.now()).update(locked=True)
    return updated
