"""URLs for DataDesk, mounted at ``/datadesk/`` when the feature flag is on."""
from django.urls import path

from datadesk.views.dashboard import DashboardView

app_name = "datadesk"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]
