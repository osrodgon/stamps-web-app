from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from countries_api.models import Country

class CountryRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Country instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Country` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = Country
        fields = ['name']
        