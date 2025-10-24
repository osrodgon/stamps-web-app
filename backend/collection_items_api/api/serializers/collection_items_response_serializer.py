from rest_framework import serializers
from collection_items_api.models import CollectionItem
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer
from condition_types_api.api.serializers.condition_type_response_serializer import ConditionTypeResponseSerializer


class CollectionItemsResponseSerializer(serializers.ModelSerializer):
    collection = CollectionResponseSerializer(read_only=True)
    stamp = StampResponseSerializer(read_only=True)
    location = LocationResponseSerializer(read_only=True)
    condition_type = ConditionTypeResponseSerializer(read_only=True)

    class Meta:
        model = CollectionItem
        fields = ['id', 'collection', 'stamp', 'location', 'condition_type', 'price_paid', 'acquisition_date', 'note', 'quantity']