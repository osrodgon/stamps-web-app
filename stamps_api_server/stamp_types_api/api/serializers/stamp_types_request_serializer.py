from rest_framework import serializers

from stamp_types_api.models import StampType

class StampTypesRequestSerializer(serializers.Serializer):
    class Meta:
        model = StampType
        fields = ['name']