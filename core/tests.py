from unittest.mock import patch

from django.test import TestCase

from core.google_imports import fetch_csv_rows, import_google_data
from worldcup.models import Group, Match, Stage, Stadium, Team


class FifaImportTests(TestCase):
    @patch("core.google_imports._fetch_text")
    def test_fetch_csv_rows_parses_fifa_schedule_page(self, fetch_text_mock):
        fetch_text_mock.return_value = """
        <html>
            <body>
                <h3>FIFA World Cup 2026 Group Stage fixtures</h3>
                <h4>Thursday, 11 June 2026</h4>
                <p>Mexico v South Africa - Group A - Mexico City Stadium</p>
                <p>Korea Republic v Czechia - Group A - Estadio Guadalajara</p>
            </body>
        </html>
        """

        rows = fetch_csv_rows("https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["home_team"], "Mexico")
        self.assertEqual(rows[0]["away_team"], "South Africa")
        self.assertEqual(rows[0]["group"], "A")
        self.assertEqual(rows[0]["stadium_city"], "Mexico City")
        self.assertEqual(rows[0]["stage"], "Fase de grupos")
        self.assertEqual(rows[1]["stadium_city"], "Guadalajara")

    @patch("core.google_imports._fetch_text")
    def test_import_google_data_imports_matches_from_fifa_page(self, fetch_text_mock):
        fetch_text_mock.return_value = """
        <html>
            <body>
                <h3>FIFA World Cup 2026 Group Stage fixtures</h3>
                <h4>Friday, 12 June 2026</h4>
                <p>Canada v Bosnia and Herzegovina - Group B - Toronto Stadium</p>
                <p>USA v Paraguay - Group D - Los Angeles Stadium</p>
            </body>
        </html>
        """

        results = import_google_data(
            matches_url="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums"
        )

        self.assertEqual(results["matches"], 2)
        self.assertEqual(Match.objects.count(), 2)
        self.assertTrue(Group.objects.filter(name="B").exists())
        self.assertTrue(Group.objects.filter(name="D").exists())
        self.assertTrue(Stage.objects.filter(name="Fase de grupos", stage_type=Stage.GROUPS).exists())
        self.assertTrue(Stadium.objects.filter(name="Toronto Stadium", city="Toronto").exists())
        self.assertTrue(Team.objects.filter(name="Canada", group__name="B").exists())
        self.assertTrue(Team.objects.filter(name="USA", group__name="D").exists())

    @patch("core.google_imports._fetch_text")
    def test_fetch_csv_rows_parses_prerendered_fifa_separator(self, fetch_text_mock):
        fetch_text_mock.return_value = """
        <html>
            <body>
                <h3>FIFA World Cup 2026 Group Stage fixtures</h3>
                <h4>Thursday, 11 June 2026</h4>
                <p>Mexico v South Africa - <strong>Group A</strong> � <em>Mexico City Stadium</em></p>
            </body>
        </html>
        """

        rows = fetch_csv_rows("https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["group"], "A")
        self.assertEqual(rows[0]["stadium_name"], "Mexico City Stadium")
