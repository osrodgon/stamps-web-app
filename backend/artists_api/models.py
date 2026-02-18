from django.db import models

# Create your models here.
class Artist(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the artist."
    )

    class Meta:
        verbose_name = "Artist"
        verbose_name_plural = "Artists"

    def __str__(self):
        return self.name