from django.db import models

# Create your models here.

class Stamp(models.Model):
    """
    Represents an individual stamp, which is part of a larger issue.

    Attributes:
        issue (ForeignKey): The issue this stamp belongs to.
        edifil_code (CharField): The Edifil catalog code for the stamp.
        face_value (CharField): The denominated value printed on the stamp.
        name (CharField):   The specific name or title of the stamp, if different
                            from the issue name.
        description (CharField): A description of the stamp.
        image (ImageField): An uploaded image of the stamp.
        colors (ManyToManyField): The colors present on the stamp.
        market_value (DecimalField):    The estimated market value of this specific
                                        stamp.
        total_printed (BigIntegerField): The total number of stamps printed.
    """
    issue = models.ForeignKey(
        'issues_api.Issue', 
        on_delete=models.CASCADE,
        related_name='stamps'
    )
    edifil_code = models.CharField(max_length=255, null=True, blank=True)
    fesofi_code = models.CharField(max_length=255, null=True, blank=True)
    face_value = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='stamps/', null=True, blank=True)
    
    # This is the many-to-many relationship field.
    colors = models.ManyToManyField(
        'colors_api.Color',
        related_name='stamps'
    )
    
    market_value_mnh = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    market_value_used = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_printed = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Stamp"
        verbose_name_plural = "Stamps"
        ordering = ['issue']

    def __str__(self):
        return f"{self.edifil_code} - {self.name}"