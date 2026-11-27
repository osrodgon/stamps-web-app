from django.urls import path
from paper_types_api.api.views.paper_types_view import PaperTypesView
from paper_types_api.api.views.paper_types_by_id_view import PaperTypesByIdView

base_url = ""

urlpatterns = [
    path(base_url, PaperTypesView.as_view(), name="paper_types"),
    path(base_url + "<int:pk>", PaperTypesByIdView.as_view(), name="paper_types_by_id"),   
]