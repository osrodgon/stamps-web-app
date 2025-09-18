from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from locations_api.models import Location

class LocationRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['name']
        
