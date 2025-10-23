from rest_framework import serializers
from condition_types_api.models import ConditionType

class ConditionTypeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionType
        fields = ['id', 'name']