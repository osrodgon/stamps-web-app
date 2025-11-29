from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from print_types_api.models import PrintType

class PrintTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating PrintType instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a print type.
    """
    class Meta:
        model = PrintType
        fields = ['name']
        
