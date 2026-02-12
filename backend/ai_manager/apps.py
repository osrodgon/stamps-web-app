from django.apps import AppConfig

from common.log.log_setup import log_setup


class AiManagerConfig(AppConfig):
    name = "ai_manager"

    def ready(self):
        log_setup()  