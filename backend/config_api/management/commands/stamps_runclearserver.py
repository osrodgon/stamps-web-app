from django.core.management.base import BaseCommand
from django.core.management import call_command

from users_api.models import UserToken

# You must redefine or import your clearing logic here
def clear_tables():
    try:
        # Get model object safely
        UserToken.objects.all().delete()
        print("Cleared UserToken")
    except Exception as e:
        print(f"Failed to clear UserToken: {e}")

class Command(BaseCommand):
    help = 'Clears UserToken table to invalidate any token, then runs the standard runserver command.'

    def handle(self, *args, **options):
        # 1. Run the cleanup logic
        clear_tables()

        # 2. Call the standard runserver command
        call_command('runserver', *args, **options)