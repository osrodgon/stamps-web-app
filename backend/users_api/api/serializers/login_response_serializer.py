from rest_framework import serializers

from users_api.api.serializers.user_response_serializer import UserResponseSerializer

class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for the login response.

    This serializer defines the structure of the data returned upon a successful login,
    including the authentication token and user details.
    """
    token = serializers.CharField(help_text="Authentication token for the user.")
    user = UserResponseSerializer(help_text="Details of the logged-in user.")
