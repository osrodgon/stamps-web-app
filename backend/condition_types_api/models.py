from django.db import models

# Create your models here.
class ConditionType(models.Model):
    """Represents the condition of a stamp.

    This model serves as a lookup table for the various physical conditions
    a stamp can be in (e.g., "Mint", "Used", "Damaged").

    Attributes:
        name (CharField): The unique name of the condition type.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the condition type (e.g., 'New', 'Used', 'Refurbished')."
    )

    class Meta:
        verbose_name = "Condition Type"
        verbose_name_plural = "Condition Types"

    def __str__(self):
        return self.name