"""URLs for DataDesk, mounted at ``/datadesk/`` when the feature flag is on."""
from django.urls import path

from datadesk.views.auth import DataDeskLoginView, DataDeskLogoutView
from datadesk.views.dashboard import DashboardView
from datadesk.views.images import StampImageView
from datadesk.views.language import set_datadesk_language
from datadesk.views.workbench import WorkbenchView
from datadesk.views.workbench_api import IssueGridJsonView
from datadesk.views.workspace import IssueWorkspaceView

app_name = "datadesk"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("issues/", WorkbenchView.as_view(), name="issues"),
    path("issues/<int:pk>/", IssueWorkspaceView.as_view(), name="issue_workspace"),
    path("stamps/<int:pk>/image", StampImageView.as_view(), name="stamp_image"),
    path("grid/issues", IssueGridJsonView.as_view(), name="issue_grid"),
    path("login/", DataDeskLoginView.as_view(), name="login"),
    path("logout/", DataDeskLogoutView.as_view(), name="logout"),
    path("language/", set_datadesk_language, name="language"),
]
