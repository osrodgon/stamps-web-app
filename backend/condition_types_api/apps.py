from django.apps import AppConfig

from common.log.log_setup import log_setup


class ConditionTypesApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "condition_types_api"
    
    def ready(self):
        log_setup()        

