from django.db import models

class Collection(models.Model):
    api_key_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        
    def __str__(self):
        return f"{self.api_key_name} - {self.name}"

