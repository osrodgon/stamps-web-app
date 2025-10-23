from rest_framework import serializers
from condition_types_api.models import ConditionType
from common.api.serializers.generic_serializer import GenericSerializer

class ConditionTypeRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = ConditionType
        fields = ['name']