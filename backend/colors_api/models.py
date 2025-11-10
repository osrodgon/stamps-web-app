from django.db import models

# Create your models here.
class Color(models.Model):
    """Represents a color used for stamps.

    This model serves as a lookup table for the various colors that can be
    associated with a stamp.

    Attributes:
        name (CharField): The unique name of the color (e.g., "Red", "Blue").
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the color (e.g., 'Red', 'Blue', 'Green')."
    )

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colors"

    def __str__(self):
        return self.name