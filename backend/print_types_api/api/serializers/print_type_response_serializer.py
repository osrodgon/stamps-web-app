from rest_framework import serializers

from print_types_api.models import PrintType

class PrintTypeResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing PrintType instances in responses.

    This serializer formats the PrintType model data for client-facing
    responses.
    """
    class Meta:
        model = PrintType
        fields = ['id','name']
