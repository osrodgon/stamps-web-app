from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from years_api.models import Year

class YearRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ['year']
        