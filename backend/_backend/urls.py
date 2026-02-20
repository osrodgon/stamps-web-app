from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from _backend.settings import (
    ADMIN_URL,
    COLLECTION_ITEMS_ENDPOINT,
    COLLECTIONS_ENDPOINT,
    COLORS_ENDPOINT,
    CONDITION_TYPES_ENDPOINT,
    CONFIG_ENDPOINT,
    COUNTRIES_ENDPOINT,
    HEALTH_ENDPOINT,
    ISSUES_ENDPOINT,
    LOCATIONS_ENDPOINT,
    PRINT_TYPES_ENDPOINT,
    PRINTERS_ENDPOINT,
    REDOC_ENDPOINT,
    SCHEMA_ENDPOINT, 
    SERVER_URL_V1,
    STAMP_TYPES_ENDPOINT,
    STAMPS_ENDPOINT,
    SWAGGER_ENDPOINT,
    USERS_ENDPOINT,
    YEARS_ENDPOINT,
    LOGIN_ENDPOINT,
    LOGOFF_ENDPOINT,
    AI_ISSUES_EXTRACTION_ENDPOINT,
    ARTISTS_ENDPOINT
)
from _backend.stamps_admin_site import stamps_admin_site
from health_api.api.views.health_view import HealthView
from users_api.api.views.login_view import LoginView
from users_api.api.views.logoff_view import LogoffView

urlpatterns = [
    path(ADMIN_URL, stamps_admin_site.urls),
    path(SERVER_URL_V1, include(
        [
            path(YEARS_ENDPOINT, include('years_api.urls')),
            path(CONFIG_ENDPOINT, include('config_api.urls')),
            path(STAMP_TYPES_ENDPOINT, include('stamp_types_api.urls')),
            path(PRINT_TYPES_ENDPOINT, include('print_types_api.urls')),
            path(LOCATIONS_ENDPOINT, include('locations_api.urls')),
            path(COUNTRIES_ENDPOINT, include('countries_api.urls')),
            path(COLORS_ENDPOINT, include('colors_api.urls')),
            path(ARTISTS_ENDPOINT, include('artists_api.urls')),
            path(PRINTERS_ENDPOINT, include('printers_api.urls')),
            path(ISSUES_ENDPOINT, include('issues_api.urls')),
            path(STAMPS_ENDPOINT, include('stamps_api.urls')),
            path(COLLECTIONS_ENDPOINT, include('collections_api.urls')),
            path(COLLECTION_ITEMS_ENDPOINT, include('collection_items_api.urls')),
            path(CONDITION_TYPES_ENDPOINT, include('condition_types_api.urls')),
            path(USERS_ENDPOINT, include('users_api.urls')),
            # Login/Logoff
            path(LOGIN_ENDPOINT, LoginView.as_view(), name="login"),
            path(LOGOFF_ENDPOINT, LogoffView.as_view(), name="logoff"),
            # AI
            path(AI_ISSUES_EXTRACTION_ENDPOINT, include('ai_api.urls')),
            # Health
            path(HEALTH_ENDPOINT, HealthView.as_view(), name="health"),
            # Documentations
            path(SCHEMA_ENDPOINT, SpectacularAPIView.as_view(), name="schema"),
            path(SWAGGER_ENDPOINT, SpectacularSwaggerView.as_view(), name="swagger"),
            path(REDOC_ENDPOINT, SpectacularRedocView.as_view(), name="redoc")
        ]
    ))
]
