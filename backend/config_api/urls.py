from django.urls import path

from config_api.api.views.config_by_id_view import ConfigByIdView
from config_api.api.views.config_view import ConfigView

base_url = ""

urlpatterns = [
    path(base_url, ConfigView.as_view(), name="config"),
    path(base_url + '<int:pk>', ConfigByIdView.as_view(), name="config_by_id")
]