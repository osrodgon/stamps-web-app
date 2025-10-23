from django.db import models

class Collection(models.Model):
    user = models.ForeignKey(
        'users_api.UserCollection',
        on_delete=models.CASCADE,
        related_name='collections',
        null=True, # Set to null=True to allow existing rows to be updated
        blank=True
    )
    api_key_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        
    def __str__(self):
        return f"{self.api_key_name} - {self.name}"
