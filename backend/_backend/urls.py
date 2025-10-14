import os
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from _backend.stamps_admin_site import stamps_admin_site

urlpatterns = [
    path(os.getenv('ADMIN_URL', 'admin/'), stamps_admin_site.urls),
    path(os.getenv('SERVER_URL_V1', 'api/v1/'), include(
        [
            path(os.getenv('YEARS_ENDPOINT', 'years/'), include('years_api.urls')),
            path(os.getenv('CONFIG_ENDPOINT', 'config/'), include('config_api.urls')),
            path(os.getenv('STAMP_TYPES_ENDPOINT', 'stamp-types/'), include('stamp_types_api.urls')),
            path(os.getenv('PAPER_TYPES_ENDPOINT', 'paper-types/'), include('paper_types_api.urls')),
            path(os.getenv('LOCATIONS_ENDPOINT', 'locations/'), include('locations_api.urls')),
            path(os.getenv('COUNTRIES_ENDPOINT', 'countries/'), include('countries_api.urls')),
            path(os.getenv('COLORS_ENDPOINT', 'colors/'), include('colors_api.urls')),
            path(os.getenv('ISSUES_ENDPOINT', 'issues/'), include('issues_api.urls')),
            path(os.getenv('STAMPS_ENDPOINT', 'stamps/'), include('stamps_api.urls')),
            path(os.getenv('COLLECTIONS_ENDPOINT', 'collections/'), include('collections_api.urls')),
            path(os.getenv('COLLECTION_ITEMS_ENDPOINT', 'collection-items/'), include('collection_items_api.urls')),
            path(os.getenv('SCHEMA_ENDPOINT', 'schema/'), SpectacularAPIView.as_view(), name="schema"),
            path(os.getenv('SWAGGER_ENDPOINT', 'swagger/'), SpectacularSwaggerView.as_view(), name="swagger"),
            path(os.getenv('REDOC_ENDPOINT', 'redoc/'), SpectacularRedocView.as_view(), name="redoc")
        ]
    ))
]
