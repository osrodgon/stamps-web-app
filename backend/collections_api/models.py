from django.db import models

class Collection(models.Model):
    """Represents a user's personal stamp collection.

    This model links a collection to a specific user and gives it a descriptive
    name. It serves as the parent container for individual `CollectionItem`
    instances, grouping them under a single named entity.

    Attributes:
        user (ForeignKey): A reference to the `UserCollection` this collection belongs to.
        name (CharField): The name of the collection (e.g., "My Childhood Collection").
    """
    user = models.ForeignKey(
        'users_api.UserCollection',
        on_delete=models.CASCADE,
        related_name='collections',
        null=True, # Set to null=True to allow existing rows to be updated
        blank=True
    )
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        
    def __str__(self):
        return f"{self.user} - {self.name}"
