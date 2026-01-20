from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Enables PostgreSQL extensions (unaccent, trigram) safely'

    def handle(self, *args, **options):
        self.stdout.write("Checking PostgreSQL extensions...")
        
        # Extensions we want to ensure exist
        extensions = ['unaccent', 'pg_trgm']

        with connection.cursor() as cursor:
            for ext in extensions:
                try:
                    # We use IF NOT EXISTS to prevent errors if already present
                    cursor.execute(f'CREATE EXTENSION IF NOT EXISTS {ext};')
                    self.stdout.write(self.style.SUCCESS(f'Successfully enabled: {ext}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to enable {ext}: {e}'))
                    self.stdout.write(self.style.WARNING('Note: You might need superuser permissions.'))

        self.stdout.write(self.style.SUCCESS('Database setup complete.'))