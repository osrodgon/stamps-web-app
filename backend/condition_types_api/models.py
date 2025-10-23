from django.db import models

# Create your models here.
class ConditionType(models.Model):
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