from django.db import models

class Year(models.Model):
    """
    Represents a calendar year.

    This model is used to associate stamps and issues with the year they
    were published.

    Attributes:
        year (IntegerField): The unique calendar year.
    """
    year = models.IntegerField(unique=True, help_text="The calendar year a stamp or issue was published.")

    class Meta:
        verbose_name = "Year"
        verbose_name_plural = "Years"

    def __str__(self):
        return str(self.year)
