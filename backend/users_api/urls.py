from django.urls import path

from users_api.api.views.users_by_id_view import UsersByIdView
from users_api.api.views.users_view import UsersView


base_url = ""

urlpatterns = [
    path(base_url, UsersView.as_view(), name="users_collection"),
    path(base_url + '<int:pk>', UsersByIdView.as_view(), name="users_collection_by_id"),
]