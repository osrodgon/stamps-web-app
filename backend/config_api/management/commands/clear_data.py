from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Deletes all entries from all registered application tables, keeping the tables intact.'

    def handle(self, *args, **options):
        # List of apps to exclude (Django's built-in tables, etc.)
        EXCLUDED_APPS = ('admin', 'auth', 'contenttypes', 'sessions', 'drf_spectacular', 'rest_framework_api_key')
        
        self.stdout.write(self.style.WARNING('Starting database cleanup...'))
        
        # Get all models from all non-excluded apps
        models = [
            m for m in apps.get_models() 
            if m._meta.app_label not in EXCLUDED_APPS
        ]

        # Use the Django ORM to delete all objects
        for model in models:
            self.stdout.write(f'Clearing table: {model._meta.db_table}')
            model.objects.all().delete()
        
        # --- SQLite Specific: Reset Auto-Increment Counters ---
        # This is CRITICAL for SQLite to prevent primary key conflicts on re-insertion.
        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING('Resetting SQLite auto-increment sequences...'))
            for model in models:
                # The table name is model._meta.db_table
                table_name = model._meta.db_table
                
                # Check if the table exists in the sqlite_sequence table
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")

        self.stdout.write(self.style.SUCCESS('\nSuccessfully cleared all application data and reset sequences. 👍'))