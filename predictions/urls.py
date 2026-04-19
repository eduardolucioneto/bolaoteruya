from django.urls import path

from predictions.views import PredictionCreateUpdateView, PredictionHistoryView

app_name = "predictions"

urlpatterns = [
    path("", PredictionHistoryView.as_view(), name="history"),
    path("match/<int:match_id>/", PredictionCreateUpdateView.as_view(), name="predict"),
]

