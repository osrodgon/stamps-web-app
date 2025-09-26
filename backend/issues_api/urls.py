from django.urls import path

from issues_api.api.views.issues_by_id_view import IssuesByIdView
from issues_api.api.views.issues_view import IssuesView

urlpatterns = [
    path('', IssuesView.as_view(), name='countries'),
    path('<int:pk>', IssuesByIdView.as_view(), name='country_by_id')
]