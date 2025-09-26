from django.urls import path

from issues_api.api.views.issues_by_id_view import IssuesByIdView
from issues_api.api.views.issues_view import IssuesView

urlpatterns = [
    path('', IssuesView.as_view(), name='issue-list'),
    path('<int:pk>/', IssuesByIdView.as_view(), name='issue-detail')
]