from rest_framework import serializers
from paper_types_api.models import PaperType
from common.api.serializers.generic_serializer import GenericSerializer

class PaperTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for PaperType instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `PaperType` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = PaperType
        fields = ['name']