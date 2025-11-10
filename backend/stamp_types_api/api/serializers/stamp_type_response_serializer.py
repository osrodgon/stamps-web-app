from rest_framework import serializers

from stamp_types_api.models import StampType

class StampTypeResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing StampType instances in responses.

    This serializer formats the StampType model data for client-facing
    responses.
    """
    class Meta:
        model = StampType
        fields = ['id','name']