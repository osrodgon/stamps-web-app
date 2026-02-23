from django.db import models

class Config(models.Model):
    """Represents a configuration setting in the application.

    This model stores key-value pairs for application settings. Settings can be
    global or user-specific, linked via the `user` ForeignKey.

    Attributes:
        user (ForeignKey):  An optional link to a `UserCollection` instance for
                            user-specific settings.
        property (CharField): The unique name of the configuration property (key).
        value (CharField): The value of the configuration property.
    """
    user = models.ForeignKey(
        'users_api.UserCollection',
        on_delete=models.CASCADE,
        related_name='config',
        null=True, # Set to null=True to allow existing rows to be updated
        blank=True
    )
    property = models.CharField(
        unique=False, 
        max_length=255, 
        help_text="The name of the configuration property (e.g., 'theme', 'language').")
    value = models.CharField(
        max_length=255,
        help_text="The value assigned to the configuration property."
    )
    
    class Meta:
        verbose_name_plural = "Config"


    def __str__(self):
        return f"{self.property}: {self.value}"
