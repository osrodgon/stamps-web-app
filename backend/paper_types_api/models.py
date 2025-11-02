from django.db import models

# Create your models here.
class PaperType(models.Model):
    """
    Represents the type of paper a stamp is printed on.

    Examples include 'Glossy', 'Matte', 'Canvas', etc.

    Attributes:
        name (CharField): The unique name of the paper type.
    """
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="The name of the paper type (e.g., 'Glossy', 'Matte', 'Canvas')."
        )
    class Meta:
        verbose_name = "Paper Type"
        verbose_name_plural = "Paper Types"
    
    def __str__(self):
        return self.name
