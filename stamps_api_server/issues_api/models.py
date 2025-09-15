from django.db import models

class Issue(models.Model):
    year = models.ForeignKey(
        'years_api.Year', 
        on_delete=models.CASCADE,
        related_name='issues'
    )
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=255)
    total_printed = models.IntegerField(null=True, blank=True)
    market_value = models.FloatField(null=True, blank=True)
    number_owned = models.IntegerField(null=True, blank=True)
    stamp_type = models.ForeignKey(
        'stamp_types_api.StampType', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    paper_type = models.ForeignKey(
        'paper_types_api.PaperType', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    description = models.TextField(null=True, blank=True)
    location = models.ForeignKey(
        'locations_api.Location', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    country = models.ForeignKey(
        'countries_api.Country', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    note = models.TextField(null=True, blank=True)
    perforation = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        ordering = ['year']

    def __str__(self):
        return f"{self.name} ({self.year.year})"
    