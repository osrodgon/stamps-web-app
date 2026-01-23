from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Deletes a specific user by username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='The username to delete')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted user "{username}"'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))