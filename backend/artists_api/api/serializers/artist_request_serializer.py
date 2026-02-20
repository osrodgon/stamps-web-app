from rest_framework import serializers
from artists_api.models import Artist
from common.api.serializers.generic_serializer import GenericSerializer

class ArtistRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Artist instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Artist` objects. It validates the `name` field.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    class Meta:
        model = Artist
        fields = ['name']