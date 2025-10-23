from rest_framework import serializers
from users_api.models import UserCollection

class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCollection
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'registration_date', 'is_active']