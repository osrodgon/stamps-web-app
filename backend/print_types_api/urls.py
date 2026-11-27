from django.urls import path

from print_types_api.api.views.print_types_view import PrintTypesView
from print_types_api.api.views.print_types_by_id_view import PrintTypesByIdView

base_url = ""

urlpatterns = [
    path(base_url, PrintTypesView.as_view(), name="print_types"),
    path(base_url + "<int:pk>", PrintTypesByIdView.as_view(), name="print_types_by_id")
]