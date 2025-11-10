from django.urls import path
from collection_items_api.api.views.collection_items_by_id_view import CollectionItemsByIdView
from collection_items_api.api.views.collection_items_view import CollectionItemsView

base_url = ""

urlpatterns = [
    path(base_url, CollectionItemsView.as_view(), name="collection_items"),
    path(base_url + '<int:pk>', CollectionItemsByIdView.as_view(), name="collection_items_by_id"),
]