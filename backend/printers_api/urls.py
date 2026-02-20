from django.urls import path
from printers_api.api.views.printers_view import PrintersView
from printers_api.api.views.printers_by_id_view import PrintersByIdView

base_url = ""

urlpatterns = [
    path(base_url, PrintersView.as_view(), name="printers"),
    path(base_url + "<int:pk>", PrintersByIdView.as_view(), name="printers_by_id"),   
]
