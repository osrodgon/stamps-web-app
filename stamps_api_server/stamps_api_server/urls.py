"""
URL configuration for stamps_api_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path(os.getenv('ADMIN_URL'), admin.site.urls),
    path(os.getenv('SERVER_URL_V1'), include(
        [
            path(os.getenv('YEARS_ENDPOINT'), include('years_api.urls')),
            path(os.getenv('CONFIG_ENDPOINT'), include('config_api.urls')),
            path(os.getenv('STAMP_TYPES_ENDPOINT'), include('stamp_types_api.urls')),
            path(os.getenv('LOCATIONS_ENDPOINT'), include('locations_api.urls')),
            path(os.getenv('SCHEMA_ENDPOINT'), SpectacularAPIView.as_view(), name="schema"),
            path(os.getenv('SWAGGER_ENDPOINT'), SpectacularSwaggerView.as_view(), name="swagger"),
            path(os.getenv('REDOC_ENDPOINT'), SpectacularRedocView.as_view(), name="redoc")
        ]
    ))
]
