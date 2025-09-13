from rest_framework import serializers
from colors_api.models import Color

class ColorResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name']
