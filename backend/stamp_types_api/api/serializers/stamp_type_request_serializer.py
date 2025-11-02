from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from stamp_types_api.models import StampType

class StampTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating StampType instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a stamp type.
    """
    class Meta:
        model = StampType
        fields = ['name']
        
