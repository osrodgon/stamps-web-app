from rest_framework import serializers
from artists_api.models import Artist

class ArtistResponseSerializer(serializers.ModelSerializer):
    """Serializes `Artist` data for API responses.

    This serializer is designed for read operations to format `Artist`
    instances for output, providing a simple representation of the artist
    including its ID and name.
    """
    class Meta:
        model = Artist
        fields = ['id', 'name']