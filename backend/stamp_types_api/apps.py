from django.apps import AppConfig

from common.log.log_setup import log_setup


class StampTypesApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stamp_types_api"
    verbose_name = "Stamp Type"
    verbose_name_plural = "Stamp Types"
    
    def ready(self):
        log_setup()        


