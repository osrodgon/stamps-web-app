from rest_framework import serializers
from collections_api.models import Collection
from users_api.api.serializers.user_response_serializer import UserResponseSerializer

class CollectionResponseSerializer(serializers.ModelSerializer):
    """Serializes `Collection` data for API responses with nested user details.

    This serializer is designed for read operations (e.g., in GET requests) to
    format `Collection` instances for output. It provides a rich, nested JSON
    representation of the related `UserCollection` object, making the API
    response self-contained and easy for clients to consume.

    The nested `user` serializer is set to `read_only=True` as this serializer
    is not intended for write operations.
    """
    user = UserResponseSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'user', 'name']