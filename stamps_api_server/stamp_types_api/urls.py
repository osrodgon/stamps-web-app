from django.urls import path

from stamp_types_api.api.views.stamp_types_view import StampTypesView
from stamp_types_api.api.views.stamp_types_by_id_view import StampTypesByIdView

base_url = ""

urlpatterns = [
    path(base_url, StampTypesView.as_view()),
    path(base_url + "<int:pk>", StampTypesByIdView.as_view())
]