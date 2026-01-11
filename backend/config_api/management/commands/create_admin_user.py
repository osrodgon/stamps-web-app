from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

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
        password = input("Password: ")
        
        
        if not email: email = "admin@example.com"
        if not first_name: first_name = username.capitalize()
        if not last_name: last_name = "User"
        if not password:
            print("\nPassword cannot be empty")
            return
        
        UserCollection.objects.create(
            username=username,
            email = email,
            first_name = first_name,
            last_name = last_name,
            password_hash = make_password(password),
            is_admin = True
        )
        