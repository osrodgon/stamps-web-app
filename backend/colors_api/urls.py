from django.urls import path
from colors_api.api.views.colors_view import ColorsView
from colors_api.api.views.colors_by_id_view import ColorsByIdView

base_url = ""

urlpatterns = [
    path(base_url, ColorsView.as_view(), name="colors"),
    path(base_url + "<int:pk>", ColorsByIdView.as_view(), name="colors_by_id"),   
]