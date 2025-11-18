from django.apps import AppConfig

from common.log.log_setup import log_setup


class LocationsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "locations_api"

    def ready(self):
        log_setup()        
