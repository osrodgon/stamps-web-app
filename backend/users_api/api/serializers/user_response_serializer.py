from rest_framework import serializers
from users_api.models import UserCollection

class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing UserCollection instances in responses.

    This serializer formats the UserCollection model data for client-facing
    responses, excluding sensitive information like the password hash.
    """
    class Meta:
        model = UserCollection
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'registration_date', 'is_active', 'is_admin']