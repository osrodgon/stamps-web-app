from django.db import models

class Country(models.Model):
    """
    Represents a country of origin for stamp issues.

    This model serves as a lookup table for the various countries that can be
    associated with a stamp issue.

    Attributes:
        name (CharField): The unique name of the country.
    """
    name = models.CharField(max_length=255, unique=True, help_text="The name of the country.")
    
    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name
