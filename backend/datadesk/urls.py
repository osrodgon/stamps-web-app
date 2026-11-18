"""URLs for DataDesk, mounted at ``/datadesk/`` when the feature flag is on."""
from django.urls import path

from datadesk.views.auth import DataDeskLoginView, DataDeskLogoutView
from datadesk.views.dashboard import DashboardView
from datadesk.views.language import set_datadesk_language
from datadesk.views.workbench import WorkbenchView
from datadesk.views.workbench_api import IssueGridJsonView

app_name = "datadesk"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("issues/", WorkbenchView.as_view(), name="issues"),
    path("grid/issues", IssueGridJsonView.as_view(), name="issue_grid"),
    path("login/", DataDeskLoginView.as_view(), name="login"),
    path("logout/", DataDeskLogoutView.as_view(), name="logout"),
    path("language/", set_datadesk_language, name="language"),
]
