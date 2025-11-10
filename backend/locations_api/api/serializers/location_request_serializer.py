from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from locations_api.models import Location

class LocationRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating Location instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a location.
    """
    class Meta:
        model = Location
        fields = ['name']
        
