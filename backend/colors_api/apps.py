from django.apps import AppConfig

from common.log.log_setup import log_setup


class ColorsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "colors_api"
    
    def ready(self):
        log_setup()        

