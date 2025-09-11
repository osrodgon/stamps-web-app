from django.urls import path
from countries_api.api.views.countries_view import CountriesView
from countries_api.api.views.countries_by_id_view import CountriesByIdView

urlpatterns = [
    path('', CountriesView.as_view(), name='countries'),
    path('<int:pk>', CountriesByIdView.as_view(), name='country_by_id')
]