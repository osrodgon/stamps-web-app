
import os
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from _backend.stamps_admin_site import stamps_admin_site

urlpatterns = [
    path(os.getenv('ADMIN_URL'), stamps_admin_site.urls),
    path(os.getenv('SERVER_URL_V1'), include(
        [
            path(os.getenv('YEARS_ENDPOINT'), include('years_api.urls')),
            path(os.getenv('CONFIG_ENDPOINT'), include('config_api.urls')),
            path(os.getenv('STAMP_TYPES_ENDPOINT'), include('stamp_types_api.urls')),
            path(os.getenv('PAPER_TYPES_ENDPOINT'), include('paper_types_api.urls')),
            path(os.getenv('LOCATIONS_ENDPOINT'), include('locations_api.urls')),
            path(os.getenv('COUNTRIES_ENDPOINT'), include('countries_api.urls')),
            path(os.getenv('COLORS_ENDPOINT'), include('colors_api.urls')),
            path(os.getenv('STAMPS_ENDPOINT'), include('stamps_api.urls')),
            path(os.getenv('SCHEMA_ENDPOINT'), SpectacularAPIView.as_view(), name="schema"),
            path(os.getenv('SWAGGER_ENDPOINT'), SpectacularSwaggerView.as_view(), name="swagger"),
            path(os.getenv('REDOC_ENDPOINT'), SpectacularRedocView.as_view(), name="redoc")
        ]
    ))
]
