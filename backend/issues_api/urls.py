from django.urls import path

from issues_api.api.views.issues_collections_view import IssuesCollectionsView
from issues_api.api.views.issues_by_id_view import IssuesByIdView
from issues_api.api.views.issues_view import IssuesView

from _backend.settings import ISSUES_COLLECTIONS_ENDPOINT

urlpatterns = [
    path(ISSUES_COLLECTIONS_ENDPOINT, IssuesCollectionsView.as_view(), name='issue-collections'),
    path('<int:pk>/', IssuesByIdView.as_view(), name='issue-detail'),
    path('', IssuesView.as_view(), name='issue-list'),
]
