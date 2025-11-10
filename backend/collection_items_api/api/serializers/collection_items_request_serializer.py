from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from collection_items_api.models import CollectionItem

class CollectionItemsRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for CollectionItem instances.

    This serializer is designed for write operations (POST, PUT, PATCH) to create
    or update `CollectionItem` objects. It expects primary key values for the
    foreign key fields (`collection`, `stamp`, `location`, `condition_type`)
    to establish relationships.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = CollectionItem
        fields = ['collection', 'stamp', 'location', 'condition_type', 'price_paid', 'acquisition_date', 'note', 'quantity']
        