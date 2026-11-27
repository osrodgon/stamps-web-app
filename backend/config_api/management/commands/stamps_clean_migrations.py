from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Cleans all migrations and creates new ones safely'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Cleaning migrations..."))
        
        count = 0

        for root, dirs, files in os.walk(settings.BASE_DIR):
            # We only care about 'migrations' folders
            if 'migrations' in root:
                for file in files:
                    # Target .py and .pyc files, but keep __init__.py
                    if file.endswith(('.py', '.pyc')) and file != "__init__.py":
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            self.stdout.write(self.style.SUCCESS(f"✅ Deleted: {file_path}"))
                            count += 1
                        except OSError as e:
                            self.stdout.write(self.style.ERROR(f"❌ Error deleting {file_path}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✨ Cleanup complete. {count} migration files removed."))
        self.stdout.write(self.style.SUCCESS("👉 Next steps: Drop your database tables, then run 'makemigrations' and 'migrate'."))