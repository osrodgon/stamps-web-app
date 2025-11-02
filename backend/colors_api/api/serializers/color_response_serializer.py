from rest_framework import serializers
from colors_api.models import Color

class ColorResponseSerializer(serializers.ModelSerializer):
    """Serializes `Color` data for API responses.

    This serializer is designed for read operations to format `Color`
    instances for output, providing a simple representation of the color
    including its ID and name.
    """
    class Meta:
        model = Color
        fields = ['id', 'name']
