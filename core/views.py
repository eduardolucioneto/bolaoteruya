from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.views.generic import TemplateView

from core.models import PoolConfiguration
from predictions.models import Prediction
from ranking.models import UserScore
from worldcup.models import Match


class HomeView(TemplateView):
    template_name = "core/home.html"


class RegulationView(TemplateView):
    template_name = "core/regulation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = PoolConfiguration.get_solo()
        participant_count = UserScore.objects.count()
        prizes = config.calculate_prizes(participant_count) if participant_count > 0 else None
        context["config"] = config
        context["quota_price"] = config.quota_price
        context["participant_count"] = participant_count
        context["prizes"] = prizes
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_predictions = Prediction.objects.filter(user=user).select_related("match")
        context["upcoming_matches"] = Match.objects.open_for_predictions().select_related("stage", "home_team", "away_team", "stadium")[:5]
        context["recent_closed_matches"] = Match.objects.finished().select_related("stage", "home_team", "away_team")[:5]
        context["predicted_count"] = user_predictions.count()
        context["score"] = UserScore.objects.filter(user=user).first()
        context["my_recent_predictions"] = user_predictions.order_by("-submitted_at")[:5]
        context["ranking_top"] = UserScore.objects.select_related("user").order_by("position", "-total_points")[:5]
        context["my_position"] = UserScore.objects.filter(user=user).values_list("position", flat=True).first()
        context["stats"] = {
            "exact_hits": user_predictions.aggregate(total=Count("id", filter=Q(points_awarded__gte=5)))["total"],
            "points": user_predictions.aggregate(total=Sum("points_awarded"))["total"] or 0,
        }
        return context


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
