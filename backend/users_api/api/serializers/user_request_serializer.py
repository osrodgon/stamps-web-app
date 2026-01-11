from rest_framework import serializers
from users_api.models import UserCollection
from common.api.serializers.generic_serializer import GenericSerializer

class UserRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating UserCollection instances.

    This serializer handles the validation and deserialization of incoming
    data for user creation and updates. The 'password' field is write-only
    and is not included in the serialized output.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserCollection
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'is_admin']