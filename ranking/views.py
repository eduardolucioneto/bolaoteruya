from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, Sum
from django.views.generic import ListView

from core.models import PoolConfiguration
from predictions.models import Prediction
from ranking.models import UserScore


class RankingListView(LoginRequiredMixin, ListView):
    template_name = "ranking/ranking_list.html"
    context_object_name = "scores"
    paginate_by = 20

    def get_queryset(self):
        queryset = UserScore.objects.select_related("user").order_by("position", "-total_points", "-exact_hits", "-outcome_hits", "user__username")
        stage = self.request.GET.get("stage")
        if stage == "stage1":
            queryset = UserScore.objects.select_related("user").order_by("stage1_position", "-stage1_points", "-exact_hits", "user__username")
        elif stage == "stage2":
            queryset = UserScore.objects.select_related("user").order_by("stage2_position", "-stage2_points", "-exact_hits", "user__username")
        elif stage:
            return (
                Prediction.objects.filter(match__stage_id=stage)
                .values("user_id", username=models.F("user__username"))
                .annotate(
                    total_points=Sum("points_awarded"),
                    exact_hits=Count("id", filter=models.Q(predicted_home_score=models.F("match__official_home_score")) & models.Q(predicted_away_score=models.F("match__official_away_score"))),
                    outcome_hits=Count("id", filter=models.Q(points_awarded__gt=0)),
                )
                .order_by("-total_points", "-exact_hits", "-outcome_hits", "username")
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        config = PoolConfiguration.get_solo()
        participant_count = UserScore.objects.count()
        prizes = config.calculate_prizes(participant_count) if participant_count > 0 else None
        context["my_score"] = UserScore.objects.filter(user=user).first()
        context["stage_filter"] = self.request.GET.get("stage", "")
        context["prizes"] = prizes
        context["participant_count"] = participant_count
        context["quota_price"] = config.quota_price
        return context
