from turtle import st
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.admin import APIKeyModelAdmin

from artists_api.models import Artist
from paper_types_api.models import PaperType
from printers_api.models import Printer
from colors_api.models import Color
from config_api.models import Config
from countries_api.models import Country
from issues_api.models import Issue
from locations_api.models import Location
from print_types_api.models import PrintType
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from users_api.models import UserCollection, UserToken
from years_api.models import Year
from collections_api.models import Collection
from collection_items_api.models import CollectionItem
from condition_types_api.models import ConditionType

ADMIN_SITE_NAME = "Administration"
STAMPS_SITE_NAME = "Stamps App"
COLLECTION_SITE_NAME = "Collections"

CATEGORIES = {
    "User": ADMIN_SITE_NAME,
    "Group": ADMIN_SITE_NAME,
    "APIKey": ADMIN_SITE_NAME, 
    "Color": STAMPS_SITE_NAME,
    "Config": STAMPS_SITE_NAME,
    "Country": STAMPS_SITE_NAME,
    "Issue": STAMPS_SITE_NAME,
    "PrintType": STAMPS_SITE_NAME,
    "StampType": STAMPS_SITE_NAME,
    "Stamp": STAMPS_SITE_NAME,
    "Year": STAMPS_SITE_NAME,
    "UserCollection": STAMPS_SITE_NAME,
    "UserToken": STAMPS_SITE_NAME,
    "Location": COLLECTION_SITE_NAME,
    "Collection": COLLECTION_SITE_NAME,
    "CollectionItem": COLLECTION_SITE_NAME,
    "ConditionType": COLLECTION_SITE_NAME,
    "Artist": STAMPS_SITE_NAME,
    "PaperType": STAMPS_SITE_NAME,
    "Printer": STAMPS_SITE_NAME,
}

class StampsAdminSite(AdminSite):
    def get_app_list(self, request):
        """
        Sobrescribimos para agrupar modelos en sub-secciones
        dentro de "Gestión Central".
        """
        app_list = super().get_app_list(request)
        categories = {}

        # Group models by category
        for app in app_list:
            for model in app["models"]:
                category = CATEGORIES.get(model["object_name"], "Others")
                if category not in categories:
                    categories[category] = []
                categories[category].append(model)

        # Create list of models sorted by category
        admin_models = []
        admin_models.extend(categories.get(ADMIN_SITE_NAME, []))
        
        stamp_models = []
        stamp_models.extend(categories.get(STAMPS_SITE_NAME, []))
        
        collection_models = []
        collection_models.extend(categories.get(COLLECTION_SITE_NAME, []))
        
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
            },
            {
                "name": "Collections",
                "app_label": "collections",
                "app_url": "/admin/",
                "has_module_perms": True,
                "models": collection_models
            }
        ]

# Create customized admin
stamps_admin_site = StampsAdminSite(name="stamsp_app_admin")

stamps_admin_site.register(User)
stamps_admin_site.register(Group)
stamps_admin_site.register(APIKey, APIKeyModelAdmin)

# Register stamps database models
stamps_admin_site.register(Color)
stamps_admin_site.register(Config)
stamps_admin_site.register(Country)
stamps_admin_site.register(Issue)
stamps_admin_site.register(PrintType)
stamps_admin_site.register(StampType)
stamps_admin_site.register(Stamp)
stamps_admin_site.register(Year)
stamps_admin_site.register(UserCollection)
stamps_admin_site.register(UserToken)
stamps_admin_site.register(Artist)
stamps_admin_site.register(PaperType)
stamps_admin_site.register(Printer)

# Register collections database models
stamps_admin_site.register(Location)
stamps_admin_site.register(Collection)
stamps_admin_site.register(CollectionItem)
stamps_admin_site.register(ConditionType)
