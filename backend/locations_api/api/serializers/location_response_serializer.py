from rest_framework import serializers

from locations_api.models import Location

class LocationResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing Location instances in responses.

    This serializer formats the Location model data for client-facing
    responses.
    """
    class Meta:
        model = Location
        fields = ['id','name']
