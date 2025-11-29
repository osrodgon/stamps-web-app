from django.apps import AppConfig

from common.log.log_setup import log_setup


class PrintTypesApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "print_types_api"
    
    def ready(self):
        log_setup()        

