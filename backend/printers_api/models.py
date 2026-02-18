from django.db import models

# Create your models here.
class Printer(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the printer. Must be unique."
    )

    class Meta:
        verbose_name = "Printer"
        verbose_name_plural = "Printers"

    def __str__(self):
        return self.name