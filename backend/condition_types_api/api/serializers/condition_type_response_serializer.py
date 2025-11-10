from rest_framework import serializers
from condition_types_api.models import ConditionType

class ConditionTypeResponseSerializer(serializers.ModelSerializer):
    """Serializes `ConditionType` data for API responses.

    This serializer is designed for read operations to format `ConditionType`
    instances for output, providing a simple representation of the condition type
    including its ID and name.
    """
    class Meta:
        model = ConditionType
        fields = ['id', 'name']