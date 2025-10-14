from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from collection_items_api.models import CollectionItem

class CollectionItemsRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = ['collection', 'stamp']
        