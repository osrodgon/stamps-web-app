from django.urls import path

from .views.years_by_id_view import YearsByIdView
from .views.years_view import YearsView

base_url = ""

urlpatterns = [
    path(base_url, YearsView.as_view(), name="beneficiaries"),
    path(base_url + '<int:id>', YearsByIdView.as_view(), name="beneficiary"),
]