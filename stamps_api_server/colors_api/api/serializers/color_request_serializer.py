from rest_framework import serializers
from colors_api.models import Color
from common.api.serializers.generic_serializer import GenericSerializer

class ColorRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['name']
