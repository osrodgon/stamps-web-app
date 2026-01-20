from django.apps import AppConfig
from django.db.models.signals import post_migrate

from common.log.log_setup import log_setup

def enable_extensions(sender, **kwargs):
    # This runs every time you migrate
    from django.db import connection
    
    extensions = ['unaccent', 'pg_trgm']
    with connection.cursor() as cursor:
        for ext in extensions:
            try:
                # We use IF NOT EXISTS to prevent errors if already present
                cursor.execute(f'CREATE EXTENSION IF NOT EXISTS {ext};')
            except Exception as e:
                print(f'Failed to enable {ext}: {e}')
                print('Note: You might need superuser permissions.')
                

class ConfigApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "config_api"
    
    def ready(self):
        post_migrate.connect(enable_extensions, sender=self)
        log_setup()        

