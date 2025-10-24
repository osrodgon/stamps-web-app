# collection_items_api/models.py

from django.db import models

class CollectionItem(models.Model):
    collection = models.ForeignKey(
        'collections_api.Collection', 
        on_delete=models.CASCADE,
        related_name='collection_items'
    )
    
    stamp = models.ForeignKey(
        'stamps_api.Stamp', 
        on_delete=models.CASCADE,
        related_name='collected_by'
    )
    
    location = models.ForeignKey(
        'locations_api.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collection_items_location'
    )
    
    condition_type = models.ForeignKey(
        'condition_types_api.ConditionType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collection_items_condition_type'
    )
    
    price_paid = models.DecimalField(max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    acquisition_date = models.DateField(
        null=True,
        blank=True
    )
    
    note = models.TextField(
        null=True,
        blank=True
    )
    
    quantity = models.IntegerField(
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ('collection', 'stamp')
        verbose_name = "Collection Item"
        verbose_name_plural = "Collection Items"
        
    def __str__(self):
        return f"{self.collection.user} - {self.stamp.name}"