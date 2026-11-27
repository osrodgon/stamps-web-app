from rest_framework import serializers
from printers_api.models import Printer
from common.api.serializers.generic_serializer import GenericSerializer

class PrinterRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Printer instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Printer` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = Printer
        fields = ['name']
