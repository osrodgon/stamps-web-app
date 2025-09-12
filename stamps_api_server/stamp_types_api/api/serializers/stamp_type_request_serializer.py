from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from stamp_types_api.models import StampType

class StampTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = StampType
        fields = ['name']
        
