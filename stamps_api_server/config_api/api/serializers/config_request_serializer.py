from rest_framework import serializers

from config_api.models import Config


class ConfigRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['property', 'value']
        