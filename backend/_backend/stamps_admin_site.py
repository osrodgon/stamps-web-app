# core/admin.py
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.admin import APIKeyModelAdmin

from colors_api.models import Color
from config_api.models import Config
from countries_api.models import Country
from issues_api.models import Issue
from locations_api.models import Location
from paper_types_api.models import PaperType
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from years_api.models import Year


ADMIN_SITE_NAME = "Administration"
STAMPS_SITE_NAME = "Stamps App"

CATEGORIES = {
    "User": ADMIN_SITE_NAME,
    "Group": ADMIN_SITE_NAME,
    "APIKey": ADMIN_SITE_NAME, 
    "Color": STAMPS_SITE_NAME,
    "Config": STAMPS_SITE_NAME,
    "Country": STAMPS_SITE_NAME,
    "Issue": STAMPS_SITE_NAME,
    "Location": STAMPS_SITE_NAME,
    "PaperType": STAMPS_SITE_NAME,
    "StampType": STAMPS_SITE_NAME,
    "Stamp": STAMPS_SITE_NAME,
    "Year": STAMPS_SITE_NAME
}

class StampsAdminSite(AdminSite):
    def get_app_list(self, request):
        """
        Sobrescribimos para agrupar modelos en sub-secciones
        dentro de "Gestión Central".
        """
        app_list = super().get_app_list(request)
        categories = {}

        # Agrupamos modelos por categoría
        for app in app_list:
            for model in app["models"]:
                category = CATEGORIES.get(model["object_name"], "Others")
                if category not in categories:
                    categories[category] = []
                categories[category].append(model)

        # Creamos lista de modelos ordenados por categorías
        admin_models = []
        admin_models.extend(categories.get(ADMIN_SITE_NAME, []))
        
        stamp_models = []
        stamp_models.extend(categories.get(STAMPS_SITE_NAME, []))

        return [
            {
                "name": "Admin",
                "app_label": "admin",
                "app_url": "/admin/",
                "has_module_perms": True,
                "models": admin_models,
            },
            {
                "name": "Stamps App",
                "app_label": "stamps_app",
                "app_url": "/admin/",
                "has_module_perms": True,
                "models": stamp_models,
            }
        ]

# Instancia de nuestro Admin personalizado
stamps_admin_site = StampsAdminSite(name="stamsp_app_admin")

stamps_admin_site.register(User)
stamps_admin_site.register(Group)
stamps_admin_site.register(APIKey, APIKeyModelAdmin)

# Registrar todos los modelos que quieras unificar
stamps_admin_site.register(Color)
stamps_admin_site.register(Config)
stamps_admin_site.register(Country)
stamps_admin_site.register(Issue)
stamps_admin_site.register(Location)
stamps_admin_site.register(PaperType)
stamps_admin_site.register(StampType)
stamps_admin_site.register(Stamp)
stamps_admin_site.register(Year)
