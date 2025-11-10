from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from collections_api.models import Collection
from users_api.models import UserCollection

class CollectionRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """Handles validation and deserialization of incoming data for Collection instances.

    This serializer is designed for write operations (POST, PUT) to create or
    update `Collection` objects. The `user` field is automatically populated
    from the authenticated user in the view logic and is marked as `read_only`
    here to prevent it from being manually set via the request payload.

    Inherits from `GenericSerializer` to ensure consistent, standardized error
    responses across the API.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=UserCollection.objects.all(), required=False)
    
    class Meta:
        model = Collection
        fields = ['user', 'name']
        read_only_fields = ['user']
        