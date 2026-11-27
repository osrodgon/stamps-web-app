from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer


class SeriesExtractionRequestSerializer(GenericSerializer, serializers.Serializer):
    """
    Serializer for AI series extraction request data.

    This serializer handles validation and deserialization of incoming
    data for AI-powered stamp series extraction requests.
    """
    name = serializers.CharField(
        max_length=200,
        help_text="Name of the stamp series to research or the motive of one of the stamps in the serie."
    )
    date = serializers.CharField(
        help_text="Publication date of the stamp series. Any date format is accepted."
    )
    
    class Meta:
        fields = [
            'name',
            'date'
        ]
        