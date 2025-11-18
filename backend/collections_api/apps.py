from django.apps import AppConfig

from common.log.log_setup import log_setup

class CollectionsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "collections_api"
    verbose_name = "Collections"
    
    def ready(self):
        log_setup()        

