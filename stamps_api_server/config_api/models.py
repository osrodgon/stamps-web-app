from django.db import models

class Config(models.Model):
    property = models.CharField(unique=True)
    value = models.CharField()
    
    class Meta:
        verbose_name_plural = "Config"


    def __str__(self):
        return f"{self.property}: {self.value}"
