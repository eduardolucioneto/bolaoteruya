import csv

from django.contrib import admin, messages
from django.http import HttpResponse

from predictions.models import Prediction
from predictions.services import lock_expired_predictions, recalculate_match_predictions
from worldcup.models import Match


@admin.action(description="Travar palpites vencidos")
def lock_predictions(modeladmin, request, queryset):
    count = lock_expired_predictions()
    messages.success(request, f"{count} palpites travados.")


@admin.action(description="Recalcular pontuação dos palpites selecionados")
def recalculate_predictions(modeladmin, request, queryset):
    matches = queryset.values_list("match_id", flat=True).distinct()
    for match_id in matches:
        recalculate_match_predictions(Match.objects.get(pk=match_id))
    messages.success(request, "Pontuações recalculadas.")



@admin.action(description="Exportar palpites em CSV")
def export_predictions_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="palpites.csv"'
    writer = csv.writer(response)
    writer.writerow(["usuario", "partida", "placar", "pontos", "travado", "processado"])
    for prediction in queryset.select_related("user", "match"):
        writer.writerow([
            prediction.user.username,
            prediction.match.match_number,
            f"{prediction.predicted_home_score}-{prediction.predicted_away_score}",
            prediction.points_awarded,
            prediction.locked,
            prediction.processed,
        ])
    return response


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "predicted_home_score", "predicted_away_score", "locked", "points_awarded", "processed")
    list_filter = ("locked", "processed", "match__stage", "match__group")
    search_fields = ("user__username", "match__match_number")
    actions = [lock_predictions, recalculate_predictions, export_predictions_csv]
