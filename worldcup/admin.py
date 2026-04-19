import csv

from django.contrib import admin, messages
from django.http import HttpResponse

from core.admin_mixins import CsvExportAdminMixin, GoogleImportAdminMixin
from predictions.services import recalculate_match_predictions
from worldcup.models import Group, Match, Stage, Stadium, Team


def build_csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


@admin.register(Group)
class GroupAdmin(CsvExportAdminMixin, GoogleImportAdminMixin, admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    export_label = "Baixar grupos"
    export_filename = "grupos.csv"

    def build_csv_response(self, queryset):
        return build_csv_response(
            self.export_filename,
            ["grupo", "descricao", "selecoes"],
            (
                [
                    group.name,
                    group.description,
                    group.teams.count(),
                ]
                for group in queryset.prefetch_related("teams")
            ),
        )


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "stage_type")
    list_filter = ("stage_type",)
    ordering = ("order",)


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "capacity")
    search_fields = ("name", "city", "country")


@admin.register(Team)
class TeamAdmin(CsvExportAdminMixin, admin.ModelAdmin):
    list_display = ("name", "fifa_code", "group", "active")
    list_filter = ("active", "group")
    search_fields = ("name", "fifa_code")
    export_label = "Baixar tabela"
    export_filename = "tabela.csv"

    def build_csv_response(self, queryset):
        return build_csv_response(
            self.export_filename,
            ["selecao", "codigo_fifa", "grupo", "ativa"],
            (
                [
                    team.name,
                    team.fifa_code,
                    team.group.name if team.group else "",
                    "Sim" if team.active else "Nao",
                ]
                for team in queryset.select_related("group")
            ),
        )


@admin.action(description="Publicar resultados oficiais e recalcular pontuação")
def publish_official_results(modeladmin, request, queryset):
    count = 0
    for match in queryset:
        if match.official_home_score is not None and match.official_away_score is not None:
            match.finished = True
            match.status = Match.STATUS_FINISHED
            match.save(update_fields=["finished", "status"])
            recalculate_match_predictions(match)
            count += 1
    messages.success(request, f"{count} partidas processadas.")


@admin.action(description="Exportar partidas em CSV")
def export_matches_csv(modeladmin, request, queryset):
    return MatchAdmin.build_matches_csv(queryset)


@admin.register(Match)
class MatchAdmin(CsvExportAdminMixin, GoogleImportAdminMixin, admin.ModelAdmin):
    list_display = ("match_number", "stage", "group", "home_team", "away_team", "start_time", "status", "finished")
    list_filter = ("stage", "group", "status", "finished", "start_time")
    search_fields = ("match_number", "home_team__name", "away_team__name", "stadium__name")
    readonly_fields = ("is_locked_display",)
    actions = [publish_official_results, export_matches_csv]
    export_label = "Baixar jogos"
    export_filename = "jogos.csv"

    fieldsets = (
        ("Partida", {"fields": ("stage", "group", "match_number", "home_team", "away_team", "stadium", "start_time", "status")}),
        ("Resultado", {"fields": ("official_home_score", "official_away_score", "finished", "is_locked_display", "notes")}),
    )

    @staticmethod
    def build_matches_csv(queryset):
        return build_csv_response(
            "jogos.csv",
            ["numero", "fase", "grupo", "mandante", "visitante", "estadio", "inicio", "status", "placar"],
            (
                [
                    match.match_number,
                    match.stage.name,
                    match.group.name if match.group else "",
                    match.home_team.name,
                    match.away_team.name,
                    match.stadium.name,
                    match.start_time,
                    match.status,
                    f"{match.official_home_score}-{match.official_away_score}" if match.finished else "",
                ]
                for match in queryset.select_related("stage", "group", "home_team", "away_team", "stadium")
            ),
        )

    def build_csv_response(self, queryset):
        return self.build_matches_csv(queryset)

    @admin.display(description="Palpite travado")
    def is_locked_display(self, obj):
        return obj.is_locked
