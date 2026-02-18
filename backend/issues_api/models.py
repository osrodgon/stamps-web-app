from django.db import models

class Issue(models.Model):
    """
    Represents a stamp issue.

    An issue is a specific set of one or more stamps released together,
    often on a particular date to commemorate an event or as part of a
    definitive series.

    Attributes:
        year (ForeignKey): The year the issue was released.
        date (DateField): The specific date of the issue.
        name (CharField): The name or title of the issue.
        total_printed (BigIntegerField): The number of stamps printed for this issue.
        market_value (DecimalField): The estimated market value.
        stamp_type (ForeignKey): The type of stamp (e.g., definitive, commemorative).
        print_type (ForeignKey): The type of print used.
        description (TextField): A detailed description of the issue.
        country (ForeignKey): The country that released the issue.
        note (TextField): Additional notes or comments.
        perforation (CharField): The perforation measurement of the stamps.
    """
    year = models.ForeignKey(
        'years_api.Year', 
        on_delete=models.CASCADE,
        related_name='issues'
    )
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=255)
    total_printed = models.BigIntegerField(null=True, blank=True)
    market_value_mnh = models.DecimalField(max_digits=8, decimal_places=2,null=True, blank=True)
    market_value_used = models.DecimalField(max_digits=8, decimal_places=2,null=True, blank=True)
    stamp_type = models.ForeignKey(
        'stamp_types_api.StampType', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    print_type = models.ForeignKey(
        'print_types_api.PrintType', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    printer = models.ForeignKey(
        'printers_api.Printer', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='issues'
    )
    artist = models.ForeignKey(
        'artists_api.Artist', 
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
    