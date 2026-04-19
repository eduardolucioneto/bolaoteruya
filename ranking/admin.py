import csv

from django.contrib import admin
from django.http import HttpResponse

from core.admin_mixins import CsvExportAdminMixin, GoogleImportAdminMixin
from ranking.models import UserScore


@admin.register(UserScore)
class UserScoreAdmin(CsvExportAdminMixin, GoogleImportAdminMixin, admin.ModelAdmin):
    list_display = ("position", "user", "total_points", "exact_hits", "outcome_hits", "updated_at")
    search_fields = ("user__username", "user__email")
    export_label = "Baixar ranking"
    export_filename = "ranking.csv"

    def build_csv_response(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.export_filename}"'
        writer = csv.writer(response)
        writer.writerow(["posicao", "usuario", "email", "pontos", "acertos_exatos", "acertos_resultado", "atualizado_em"])
        for score in queryset.select_related("user"):
            writer.writerow([
                score.position,
                score.user.username,
                score.user.email,
                score.total_points,
                score.exact_hits,
                score.outcome_hits,
                score.updated_at,
            ])
        return response
