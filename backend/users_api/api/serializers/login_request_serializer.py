from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer

class LoginRequestSerializer(GenericSerializer, serializers.Serializer):
    """
    Serializer for handling user login requests.

    This serializer validates the username and password provided by the user
    during the login process.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
