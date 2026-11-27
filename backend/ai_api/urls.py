from django.urls import path
from ai_api.api.views.series_extraction_view import SeriesExtractionView


base_url = ""

urlpatterns = [
    path(base_url, SeriesExtractionView.as_view(), name="ai_api_series_extraction"),
]