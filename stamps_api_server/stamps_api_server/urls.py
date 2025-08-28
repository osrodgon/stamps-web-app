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
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .swagger import CustomOpenAPISchemaGenerator

schema_view = get_schema_view(
    openapi.Info(
        title="Stamps Application API",
        default_version='v1',
        description="A list of public APIs available for the Stamps application.",
        #terms_of_service="https://www.example.com/terms/",
        #contact=openapi.Contact(email="contact@example.com"),
        #license=openapi.License(name="Awesome License"),
    ),
    generator_class=CustomOpenAPISchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path(os.getenv('ADMIN_URL'), admin.site.urls),
    path(os.getenv('SERVER_URL_V1'), include(
        [
            path(os.getenv('YEARS_ENDPOINT'), include('years_api.urls')),
            path(os.getenv('CONFIG_ENDPOINT'), include('config_api.urls')),
            path(os.getenv('SWAGGER_ENDPOINT'),schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
        ]
    ))
]
