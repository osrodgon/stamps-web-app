from django.db import models

class Country(models.Model):
    name = models.IntegerField(unique=True, help_text="The country a stamp or issue was published.")

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return str(self.name)

