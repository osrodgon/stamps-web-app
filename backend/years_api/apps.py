from django.apps import AppConfig

from common.log.log_setup import log_setup


class YearsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "years_api"
    verbose_name = "Years"
    
    def ready(self):
        log_setup()        

