from django.urls import path

from worldcup.views import MatchDetailView, MatchListView, TableView

app_name = "worldcup"

urlpatterns = [
    path("matches/", MatchListView.as_view(), name="match_list"),
    path("matches/<int:pk>/", MatchDetailView.as_view(), name="match_detail"),
    path("table/", TableView.as_view(), name="table"),
]

