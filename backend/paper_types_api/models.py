from django.db import models

# Create your models here.
class PaperType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the paper type (e.g., 'Matte', 'Glossy', 'Lustre')."
    )

    class Meta:
        verbose_name = "Paper Type"
        verbose_name_plural = "Paper Types"

    def __str__(self):
        return self.name
    