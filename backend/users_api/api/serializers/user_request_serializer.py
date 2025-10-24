from rest_framework import serializers
from users_api.models import UserCollection
from common.api.serializers.generic_serializer import GenericSerializer

class UserRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserCollection
        fields = ['username', 'email', 'password', 'first_name', 'last_name']