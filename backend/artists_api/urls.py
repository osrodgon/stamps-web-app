from django.urls import path
from artists_api.api.views.artists_view import ArtistsView
from artists_api.api.views.artists_by_id_view import ArtistsByIdView

base_url = ""

urlpatterns = [
    path(base_url, ArtistsView.as_view(), name="artists"),
    path(base_url + "<int:pk>", ArtistsByIdView.as_view(), name="artists_by_id"),   
]