from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from config_api.models import Config


class ConfigRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Config instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Config` objects. It validates the `user`, `property`, and `value`
    fields.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = Config
        fields = ['user', 'property', 'value']
        
