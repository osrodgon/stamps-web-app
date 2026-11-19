"""URLs for DataDesk, mounted at ``/datadesk/`` when the feature flag is on.

The JSON endpoints carry no trailing slash, like ``grid/issues``: they are
fetched by the page scripts, never typed by a human.
"""

from django.urls import path

from datadesk.views.auth import DataDeskLoginView, DataDeskLogoutView
from datadesk.views.dashboard import DashboardView
from datadesk.views.images import StampImageView
from datadesk.views.language import set_datadesk_language
from datadesk.views.workbench import WorkbenchView
from datadesk.views.workbench_api import IssueGridJsonView
from datadesk.views.workspace import IssueNewView, IssueWorkspaceView
from datadesk.views.write_api import (
    ApplyJsonView,
    IssueCreateJsonView,
    LookupCreateJsonView,
)

app_name = "datadesk"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("issues/", WorkbenchView.as_view(), name="issues"),
    path("issues/new/", IssueNewView.as_view(), name="issue_new"),
    path("issues/<int:pk>/", IssueWorkspaceView.as_view(), name="issue_workspace"),
    path("stamps/<int:pk>/image", StampImageView.as_view(), name="stamp_image"),
    path("grid/issues", IssueGridJsonView.as_view(), name="issue_grid"),
    path("issues/create", IssueCreateJsonView.as_view(), name="issue_create"),
    path("apply", ApplyJsonView.as_view(), name="apply"),
    path(
        "lookups/<str:key>/create",
        LookupCreateJsonView.as_view(),
        name="lookup_create",
    ),
    path("login/", DataDeskLoginView.as_view(), name="login"),
    path("logout/", DataDeskLogoutView.as_view(), name="logout"),
    path("language/", set_datadesk_language, name="language"),
]
