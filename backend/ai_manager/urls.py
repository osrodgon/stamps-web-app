from django.urls import path
from ai_manager.api.views.research_series_view import ResearchSeriesView


base_url = ""

urlpatterns = [
    path(base_url, ResearchSeriesView.as_view(), name="ai_manager"),
]