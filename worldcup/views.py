from django.db import models
from django.db.models import Count
from django.views.generic import DetailView, ListView, TemplateView

from worldcup.models import Match, Team


class MatchListView(ListView):
    model = Match
    template_name = "worldcup/match_list.html"
    context_object_name = "matches"
    paginate_by = 10

    def get_queryset(self):
        queryset = Match.objects.select_related("stage", "group", "home_team", "away_team", "stadium")
        stage = self.request.GET.get("stage")
        group = self.request.GET.get("group")
        if stage:
            queryset = queryset.filter(stage_id=stage)
        if group:
            queryset = queryset.filter(group_id=group)
        return queryset.order_by("start_time")


class MatchDetailView(DetailView):
    model = Match
    template_name = "worldcup/match_detail.html"
    context_object_name = "match"

    def get_queryset(self):
        return Match.objects.select_related("stage", "group", "home_team", "away_team", "stadium")


class TeamDetailView(DetailView):
    model = Team
    template_name = "worldcup/team_detail.html"
    context_object_name = "team"

    def get_queryset(self):
        return Team.objects.select_related("group")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        context["matches"] = Match.objects.select_related("stage", "group", "home_team", "away_team", "stadium").filter(
            models.Q(home_team=team) | models.Q(away_team=team)
        ).order_by("start_time")
        return context


class TableView(TemplateView):
    template_name = "worldcup/table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teams = Team.objects.select_related("group").filter(group__isnull=False).order_by("group__name", "position", "name")
        groups = {}
        for team in teams:
            g = team.group.name
            if g not in groups:
                groups[g] = []
            groups[g].append(team)
        context["teams"] = teams
        context["groups"] = groups
        return context
