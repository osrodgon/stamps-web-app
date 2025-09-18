from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="The name of the location (e.g., 'Album 1', 'Stockbook').")
    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return self.name
