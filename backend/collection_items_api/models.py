# collection_items_api/models.py

from django.db import models

CONDITION_CHOICES = (
    # ... (Define you conditions here)
)

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
    
    class Meta:
        unique_together = ('collection', 'stamp')
        verbose_name = "Collection Item"
        verbose_name_plural = "Collection Items"
        
    def __str__(self):
        return f"{self.collection.user} - {self.stamp.name}"