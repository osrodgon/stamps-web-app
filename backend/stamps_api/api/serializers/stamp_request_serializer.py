from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from stamps_api.models import Stamp


class StampRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating Stamp instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a stamp.
    """
    class Meta:
        model = Stamp
        fields = [
            'issue',
            'edifil_code',
            'face_value',
            'name',
            'description',
            'image',
            'colors',
            'market_value'
        ]
        
        extra_kwargs = {
            'extra': {'allow_extra_fields': False}
        }
        