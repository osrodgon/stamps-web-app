from rest_framework import serializers
from paper_types_api.models import PaperType

class PaperTypeResponseSerializer(serializers.ModelSerializer):
    """Serializes `PaperType` data for API responses.

    This serializer is designed for read operations to format `PaperType`
    instances for output, providing a simple representation of the paper type
    including its ID and name.
    """
    class Meta:
        model = PaperType
        fields = ['id', 'name']