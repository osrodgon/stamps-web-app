from django.urls import path

from collections_api.api.views.collection_catalogue_issue_detail_view import (
    CollectionCatalogueIssueDetailView,
)
from collections_api.api.views.collection_catalogue_issues_view import (
    CollectionCatalogueIssuesView,
)
from collections_api.api.views.collection_issue_detail_view import (
    CollectionIssueDetailView,
)
from collections_api.api.views.collection_issue_items_view import (
    CollectionIssueItemsView,
)
from collections_api.api.views.collection_items_bulk_view import (
    CollectionItemsBulkView,
)
from collections_api.api.views.collection_issues_view import CollectionIssuesView
from collections_api.api.views.collections_by_id_view import CollectionsByIdView
from collections_api.api.views.collections_view import CollectionsView

base_url = ""

urlpatterns = [
    path(base_url, CollectionsView.as_view(), name="collections"),
    path(base_url + '<int:pk>', CollectionsByIdView.as_view(), name="collection_by_id"),
    path(
        base_url + '<int:pk>/issues/',
        CollectionIssuesView.as_view(),
        name="collection_issues",
    ),
    path(
        base_url + '<int:pk>/issues/<int:issue_pk>/',
        CollectionIssueDetailView.as_view(),
        name="collection_issue_detail",
    ),
    path(
        base_url + '<int:pk>/catalogue/issues/',
        CollectionCatalogueIssuesView.as_view(),
        name="collection_catalogue",
    ),
    path(
        base_url + '<int:pk>/catalogue/issues/<int:issue_pk>/',
        CollectionCatalogueIssueDetailView.as_view(),
        name="collection_catalogue_issue_detail",
    ),
    path(
        base_url + '<int:pk>/items/',
        CollectionIssueItemsView.as_view(),
        name="collection_item_add",
    ),
    path(
        base_url + '<int:pk>/items/bulk/',
        CollectionItemsBulkView.as_view(),
        name="collection_items_bulk_add",
    ),
]