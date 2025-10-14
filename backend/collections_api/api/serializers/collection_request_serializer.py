from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from collections_api.models import Collection

class CollectionRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['name']
        