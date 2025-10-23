from django.db import models

# Create your models here.

class Stamp(models.Model):
    issue = models.ForeignKey(
        'issues_api.Issue', 
        on_delete=models.CASCADE,
        related_name='stamps'
    )
    edifil_code = models.CharField(max_length=255, null=True, blank=True)
    face_value = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    others_code = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='stamps/', null=True, blank=True)
    
    # This is the many-to-many relationship field.
    colors = models.ManyToManyField(
        'colors_api.Color',
        related_name='stamps'
    )
    
    market_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = "Stamp"
        verbose_name_plural = "Stamps"
        ordering = ['issue']

    def __str__(self):
        return f"{self.edifil_code} - {self.name}"