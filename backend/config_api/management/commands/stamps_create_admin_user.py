from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from getpass import getpass

from users_api.models import UserCollection

class Command(BaseCommand):
    help = 'Creates and admin user.'
    
    def handle(self, *args, **options):
        print("Create and admin user. Please enter the requested data:\n")
        username = input("User name (admin): ")
        if not username: username = "admin"
        email = input(f"Email ({username}@example.com): ")
        first_name = input(f"First name ({username.capitalize()}): ")
        last_name = input("Last name (User): ")
        password = getpass("Password: ")
        
        
        if not email: email = f"{username}@example.com"
        if not first_name: first_name = username.capitalize()
        if not last_name: last_name = "User"
        if not password:
            print("\nPassword cannot be empty")
            return
        
        try:
            UserCollection.objects.create(
                username=username,
                email = email,
                first_name = first_name,
                last_name = last_name,
                password_hash = make_password(password),
                is_admin = True
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created admin user '{username}'."))
        except Exception as e:
            self.stderr.write(self.style.ERROR("A user with this username or email already exists."))
            self.stderr.write(self.style.ERROR(str(e)))
        