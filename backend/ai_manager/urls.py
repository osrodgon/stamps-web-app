from django.urls import path
from ai_manager.api.views.ai_manager_view import AIManagerView


base_url = ""

urlpatterns = [
    path(base_url, AIManagerView.as_view(), name="ai_manager"),
]