from django.urls import path

from years_api.api.views.years_by_id_view import YearsByIdView
from years_api.api.views.years_view import YearsView

base_url = ""

urlpatterns = [
    path(base_url, YearsView.as_view(), name="years"),
    path(base_url + '<int:pk>', YearsByIdView.as_view(), name="year"),
]