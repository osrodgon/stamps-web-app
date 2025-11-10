from rest_framework import serializers
from condition_types_api.models import ConditionType
from common.api.serializers.generic_serializer import GenericSerializer

class ConditionTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for ConditionType instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `ConditionType` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = ConditionType
        fields = ['name']