from django import forms

from predictions.models import Prediction


class PredictionForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ("predicted_home_score", "predicted_away_score")
        labels = {
            "predicted_home_score": "Palpite Time Casa",
            "predicted_away_score": "Palpite Time Visitante",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.match = kwargs.pop("match")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.match = self.match
        if commit:
            instance.save()
        return instance
