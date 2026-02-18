from django.apps import AppConfig

from common.log.log_setup import log_setup

class PaperTypesApiConfig(AppConfig):
    name = "paper_types_api"

    def ready(self):
        log_setup()