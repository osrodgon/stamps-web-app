"""URLs for DataDesk, mounted at ``/datadesk/`` when the feature flag is on.

The JSON endpoints carry no trailing slash, like ``grid/issues``: they are
fetched by the page scripts, never typed by a human.
"""

from django.urls import path

from datadesk.views.auth import DataDeskLoginView, DataDeskLogoutView
from datadesk.views.dashboard import DashboardView
from datadesk.views.images import StampImageView
from datadesk.views.language import set_datadesk_language
from datadesk.views.lookups import (
    LookupDeleteJsonView,
    LookupIndexView,
    LookupMergeJsonView,
    LookupNextYearsJsonView,
    LookupRenameJsonView,
    LookupRowsJsonView,
    LookupTableView,
)
from datadesk.views.workbench import WorkbenchView
from datadesk.views.workbench_api import IssueGridJsonView
from datadesk.views.workspace import IssueNewView, IssueWorkspaceView
from datadesk.views.write_api import (
    ApplyJsonView,
    BackupJsonView,
    IssueCloneJsonView,
    IssueCreateJsonView,
    IssueDeleteJsonView,
    IssueDependenciesJsonView,
    LookupCreateJsonView,
    LookupSearchJsonView,
)

app_name = "datadesk"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("issues/", WorkbenchView.as_view(), name="issues"),
    path("issues/new/", IssueNewView.as_view(), name="issue_new"),
    path("issues/<int:pk>/", IssueWorkspaceView.as_view(), name="issue_workspace"),
    path("stamps/<int:pk>/image", StampImageView.as_view(), name="stamp_image"),
    path("lookups/", LookupIndexView.as_view(), name="lookups"),
    path("lookups/merge", LookupMergeJsonView.as_view(), name="lookup_merge"),
    path(
        "lookups/years/next",
        LookupNextYearsJsonView.as_view(),
        name="lookup_next_years",
    ),
    path("lookups/<str:key>/", LookupTableView.as_view(), name="lookups_table"),
    path("lookups/<str:key>/rows", LookupRowsJsonView.as_view(), name="lookup_rows"),
    path(
        "lookups/<str:key>/rename",
        LookupRenameJsonView.as_view(),
        name="lookup_rename",
    ),
    path(
        "lookups/<str:key>/delete",
        LookupDeleteJsonView.as_view(),
        name="lookup_delete",
    ),
    path("grid/issues", IssueGridJsonView.as_view(), name="issue_grid"),
    path("issues/create", IssueCreateJsonView.as_view(), name="issue_create"),
    path("issues/<int:pk>/clone", IssueCloneJsonView.as_view(), name="issue_clone"),
    path(
        "issues/<int:pk>/dependencies",
        IssueDependenciesJsonView.as_view(),
        name="issue_dependencies",
    ),
    path("issues/<int:pk>/delete", IssueDeleteJsonView.as_view(), name="issue_delete"),
    path("apply", ApplyJsonView.as_view(), name="apply"),
    path("backup", BackupJsonView.as_view(), name="backup"),
    path(
        "lookups/<str:key>/create",
        LookupCreateJsonView.as_view(),
        name="lookup_create",
    ),
    path(
        "lookups/<str:key>/search",
        LookupSearchJsonView.as_view(),
        name="lookup_search",
    ),
    path("login/", DataDeskLoginView.as_view(), name="login"),
    path("logout/", DataDeskLogoutView.as_view(), name="logout"),
    path("language/", set_datadesk_language, name="language"),
]
