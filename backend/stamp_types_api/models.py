from django.db import models

class StampType(models.Model):
    """
    Represents a type of stamp.

    Examples include 'Definitive', 'Commemorative', 'Postage Due', etc.

    Attributes:
        name (CharField): The unique name of the stamp type.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The name of the stamp type (e.g., 'Definitive', 'Commemorative').")
    
    class Meta:
        verbose_name = "Stamp Type"
        verbose_name_plural = "Stamp Types"

    def __str__(self):
        return self.name
