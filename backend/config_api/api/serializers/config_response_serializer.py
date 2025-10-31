from rest_framework import serializers

from config_api.models import Config


class ConfigResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['id', 'user', 'property', 'value']
