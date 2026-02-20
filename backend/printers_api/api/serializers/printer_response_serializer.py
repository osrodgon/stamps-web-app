from rest_framework import serializers
from printers_api.models import Printer

class PrinterResponseSerializer(serializers.ModelSerializer):
    """Serializes `Printer` data for API responses.

    This serializer is designed for read operations to format `Printer`
    instances for output, providing a simple representation of the printer
    including its ID and name.
    """
    class Meta:
        model = Printer
        fields = ['id', 'name']
