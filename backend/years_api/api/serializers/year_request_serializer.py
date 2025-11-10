from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from years_api.models import Year

class YearRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating Year instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a year.
    """
    class Meta:
        model = Year
        fields = ['year']
        