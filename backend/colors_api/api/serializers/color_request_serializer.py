from rest_framework import serializers
from colors_api.models import Color
from common.api.serializers.generic_serializer import GenericSerializer

class ColorRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Color instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Color` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = Color
        fields = ['name']
