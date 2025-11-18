from django.apps import AppConfig

from common.log.log_setup import log_setup


class StampsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stamps_api"

    def ready(self):
        log_setup()        
