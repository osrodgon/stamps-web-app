from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer


class SeriesExtractionRequestSerializer(GenericSerializer, serializers.Serializer):
    """
    Serializer for AI series extraction request data.

    This serializer handles validation and deserialization of incoming
    data for AI-powered stamp series extraction requests.
    """
    issue_name = serializers.CharField(
        max_length=200,
        help_text="Name of the stamp series to research"
    )
    issue_date = serializers.CharField(
        help_text="Publication date of the stamp series. Any date format is accepted."
    )
    edifil_start_number = serializers.CharField(
        max_length=10,
        required=False,    # Optional field
        allow_blank=True,  # Allow empty string if provided
        default=None,      # Set default to None
        help_text="Starting Edifil catalog number for the series (optional)"
    )
    
    class Meta:
        fields = [
            'issue_name',
            'issue_date', 
            'edifil_start_number'
        ]
        