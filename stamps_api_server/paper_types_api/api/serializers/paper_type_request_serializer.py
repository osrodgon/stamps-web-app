from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from paper_types_api.models import PaperType

class PaperTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = PaperType
        fields = ['name']
        
