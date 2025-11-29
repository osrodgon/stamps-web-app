from django.db import models

# Create your models here.
class PrintType(models.Model):
    """
    Represents the type of print used in a stamp.

    Examples include 'Glossy', 'Matte', 'Canvas', etc.

    Attributes:
        name (CharField): The unique name of the print type.
    """
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="The name of the print type (e.g., 'Glossy', 'Matte', 'Canvas')."
        )
    class Meta:
        verbose_name = "Print Type"
        verbose_name_plural = "Print Types"
    
    def __str__(self):
        return self.name
