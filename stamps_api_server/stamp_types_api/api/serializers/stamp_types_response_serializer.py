from rest_framework import serializers

from stamp_types_api.models import StampType

class StampTypesResponseSerializer(serializers.Serializer):
    class Meta:
        model = StampType
        fields = ['id','name']