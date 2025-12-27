from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Deletes all entries and resets sequences for PostgreSQL tables.'

    def handle(self, *args, **options):
        EXCLUDED_APPS = ('admin', 'auth', 'contenttypes', 'sessions', 'drf_spectacular', 'rest_framework_api_key')
        
        self.stdout.write(self.style.WARNING('Starting PostgreSQL database cleanup...'))
        
        # Collect table names from non-excluded apps
        table_names = [
            model._meta.db_table for model in apps.get_models() 
            if model._meta.app_label not in EXCLUDED_APPS
        ]

        if not table_names:
            self.stdout.write("No tables found to clear.")
            return

        # PostgreSQL specific: TRUNCATE with RESTART IDENTITY
        # 'CASCADE' handles foreign key dependencies automatically
        # 'RESTART IDENTITY' resets the auto-increment sequences
        truncate_query = f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE;"

        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING(f'Truncating {len(table_names)} tables...'))
            cursor.execute(truncate_query)

        self.stdout.write(self.style.SUCCESS('Successfully cleared all data and reset PostgreSQL sequences.'))