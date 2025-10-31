from django.db import models

class Config(models.Model):
    user = models.ForeignKey(
        'users_api.UserCollection',
        on_delete=models.CASCADE,
        related_name='config',
        null=True, # Set to null=True to allow existing rows to be updated
        blank=True
    )
    property = models.CharField(
        unique=True, 
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
