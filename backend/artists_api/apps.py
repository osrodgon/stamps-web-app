from django.apps import AppConfig

from common.log.log_setup import log_setup


class ArtistApiConfig(AppConfig):
    name = "artists_api"

    def ready(self):
        log_setup()
