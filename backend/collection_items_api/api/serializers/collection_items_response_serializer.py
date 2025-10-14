from rest_framework import serializers
from collection_items_api.models import CollectionItem
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer


class CollectionItemsResponseSerializer(serializers.ModelSerializer):
    collection = CollectionResponseSerializer(read_only=True)
    stamp = StampResponseSerializer(read_only=True)

    class Meta:
        model = CollectionItem
        fields = ['id', 'collection', 'stamp']