from django.urls import path

from locations_api.api.views.locations_view import LocationsView
from locations_api.api.views.locations_by_id_view import LocationsByIdView

base_url = ""

urlpatterns = [
    path(base_url, LocationsView.as_view(), name="locations"),
    path(base_url + "<int:pk>", LocationsByIdView.as_view(), name="locations_by_id")
]
