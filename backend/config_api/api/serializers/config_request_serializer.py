from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from config_api.models import Config


class ConfigRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['user', 'property', 'value']
        
