from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from paper_types_api.models import PaperType

class PaperTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating PaperType instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating a paper type.
    """
    class Meta:
        model = PaperType
        fields = ['name']
        
