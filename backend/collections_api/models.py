from django.db import models

class Collection(models.Model):
    user = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    # ... Other fields
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        
    def __str__(self):
        return f"{self.user} - {self.name}"

