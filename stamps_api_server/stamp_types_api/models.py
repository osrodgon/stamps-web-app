from django.db import models

class StampType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="The name of the stamp type (e.g., 'Definitive', 'Commemorative').")
    
    class Meta:
        verbose_name = "Stamp Type"
        verbose_name_plural = "Stamp Types"

    def __str__(self):
        return self.name
