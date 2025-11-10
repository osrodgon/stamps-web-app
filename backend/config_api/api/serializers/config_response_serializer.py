from rest_framework import serializers

from config_api.models import Config


class ConfigResponseSerializer(serializers.ModelSerializer):
    """Serializes `Config` data for API responses.

    This serializer is designed for read operations to format `Config`
    instances for output, providing a representation of the configuration
    entry including its ID, user, property, and value.
    """
    class Meta:
        model = Config
        fields = ['id', 'user', 'property', 'value']
