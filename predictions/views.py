from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from predictions.forms import PredictionForm
from predictions.models import Prediction
from worldcup.models import Match


class PredictionHistoryView(LoginRequiredMixin, ListView):
    template_name = "predictions/prediction_history.html"
    context_object_name = "predictions"
    paginate_by = 15

    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user).select_related("match", "match__stage", "match__home_team", "match__away_team")


class PredictionCreateUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "predictions/prediction_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.match = get_object_or_404(Match.objects.select_related("home_team", "away_team", "stage"), pk=kwargs["match_id"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        prediction = Prediction.objects.filter(user=request.user, match=self.match).first()
        form = PredictionForm(instance=prediction, user=request.user, match=self.match)
        return self.render_to_response({"form": form, "match": self.match, "prediction": prediction})

    def post(self, request, *args, **kwargs):
        prediction = Prediction.objects.filter(user=request.user, match=self.match).first()
        form = PredictionForm(request.POST, instance=prediction, user=request.user, match=self.match)
        if form.is_valid():
            form.save()
            messages.success(request, "Palpite salvo com sucesso.")
            return redirect("predictions:history")
        return self.render_to_response({"form": form, "match": self.match, "prediction": prediction})

