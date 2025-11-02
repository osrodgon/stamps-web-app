from django.db import models

class UserCollection(models.Model):
    """
    Represents a user in the collection management system.

    Attributes:
        username (CharField): The unique username for the user.
        email (EmailField): The unique email address for the user.
        password_hash (CharField): The hashed password for the user.
        first_name (CharField): The user's first name.
        last_name (CharField): The user's last name.
        registration_date (DateTimeField): The date and time the user registered.
        is_active (BooleanField):   Designates whether this user should be treated as
                                    active.
    """
    username = models.CharField(max_length=100, unique=True, blank=False, null=False)
    email = models.EmailField(max_length=100, unique=True, blank=False, null=False)
    password_hash = models.CharField(max_length=100, blank=False, null=False)
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.username
    