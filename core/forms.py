from django import forms


class GoogleImportForm(forms.Form):
    groups_sheet_url = forms.URLField(
        label="URL Google Sheets - Grupos",
        required=False,
        help_text="Planilha publicada em CSV com colunas: name, description",
    )
    matches_sheet_url = forms.URLField(
        label="URL Google Sheets - Jogos",
        required=False,
        help_text=(
            "Aceita CSV, Google Sheets publicado em CSV ou a URL oficial da FIFA do calendario. "
            "Colunas minimas no CSV: match_number, stage, home_team, away_team, stadium_name, "
            "stadium_city, start_time. Opcionais: group, status, official_home_score, "
            "official_away_score, finished, notes, stage_order, stage_type, fifa_code_home, "
            "fifa_code_away, stadium_country, stadium_capacity"
        ),
    )
    ranking_sheet_url = forms.URLField(
        label="URL Google Sheets - Ranking",
        required=False,
        help_text="Colunas minimas: username ou email, total_points. Opcionais: exact_hits, outcome_hits, position",
    )

    def clean(self):
        cleaned_data = super().clean()
        if not any(
            cleaned_data.get(field_name)
            for field_name in ("groups_sheet_url", "matches_sheet_url", "ranking_sheet_url")
        ):
            raise forms.ValidationError("Informe ao menos uma URL para importar.")
        return cleaned_data
