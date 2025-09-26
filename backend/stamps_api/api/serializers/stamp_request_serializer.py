from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from stamps_api.models import Stamp


class StampRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Stamp
        fields = [
            'issue',
            'edifil_code',
            'face_value',
            'name',
            'others_code',
            'image',
            'colors',
            'market_value'
        ]
        
        extra_kwargs = {
            'extra': {'allow_extra_fields': False}
        }
        
    # def validate(self, data):
    #     super().validate(data)
    #     return data