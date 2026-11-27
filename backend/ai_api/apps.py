from django.apps import AppConfig

from common.log.log_setup import log_setup


class AIApiConfig(AppConfig):
    name = "ai_api"

    def ready(self):
        log_setup()  