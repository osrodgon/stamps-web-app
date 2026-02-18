from django.apps import AppConfig

from common.log.log_setup import log_setup

class PrinterApiConfig(AppConfig):
    name = "printers_api"
    
    def ready(self):
        log_setup()
        
