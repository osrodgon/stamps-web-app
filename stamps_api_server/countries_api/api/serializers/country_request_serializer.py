from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from countries_api.models import Country

class CountryRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name']
        