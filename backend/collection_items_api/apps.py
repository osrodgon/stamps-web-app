from django.apps import AppConfig

from common.log.log_setup import log_setup

class CollectionItemsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "collection_items_api"
    
    def ready(self):
        log_setup()        
