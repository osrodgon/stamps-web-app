from rest_framework import serializers
from collections_api.models import Collection
from users_api.api.serializers.user_response_serializer import UserResponseSerializer

class CollectionResponseSerializer(serializers.ModelSerializer):
    user = UserResponseSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'user', 'name']