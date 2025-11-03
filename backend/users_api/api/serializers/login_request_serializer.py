from rest_framework import serializers

class LoginRequestSerializer(serializers.Serializer):
    """
    Serializer for handling user login requests.

    This serializer validates the username and password provided by the user
    during the login process.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)