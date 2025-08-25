from django.db import models

class Year(models.Model):
    year = models.IntegerField(help_text="Year the stamp or issue where published.")

    class Meta:
        verbose_name_plural = "Years"

    def __str__(self):
        return self.year
