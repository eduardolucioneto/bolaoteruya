from django.urls import path

from core.views import DashboardView, HomeView, RegulationView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("regulamento/", RegulationView.as_view(), name="regulation"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
