from django.urls import path

from collections_api.api.views.collections_by_id_view import CollectionsByIdView
from collections_api.api.views.collections_view import CollectionsView

base_url = ""

urlpatterns = [
    path(base_url, CollectionsView.as_view(), name="collections"),
    path(base_url + '<int:pk>', CollectionsByIdView.as_view(), name="collection_by_id"),
]