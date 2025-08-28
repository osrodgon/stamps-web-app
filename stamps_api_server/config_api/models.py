from django.db import models

class Config(models.Model):
    property = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.property}: {self.value}"
from django.db import models

# Create your models here.
