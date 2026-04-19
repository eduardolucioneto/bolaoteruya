from django.db.models import Count
from django.views.generic import DetailView, ListView, TemplateView

from worldcup.models import Match, Team


class MatchListView(ListView):
    model = Match
    template_name = "worldcup/match_list.html"
    context_object_name = "matches"
    paginate_by = 12

    def get_queryset(self):
        queryset = Match.objects.select_related("stage", "group", "home_team", "away_team", "stadium")
        stage = self.request.GET.get("stage")
        group = self.request.GET.get("group")
        if stage:
            queryset = queryset.filter(stage_id=stage)
        if group:
            queryset = queryset.filter(group_id=group)
        return queryset


class MatchDetailView(DetailView):
    model = Match
    template_name = "worldcup/match_detail.html"
    context_object_name = "match"

    def get_queryset(self):
        return Match.objects.select_related("stage", "group", "home_team", "away_team", "stadium")


class TableView(TemplateView):
    template_name = "worldcup/table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teams"] = Team.objects.select_related("group").order_by("group__name", "name")
        return context
