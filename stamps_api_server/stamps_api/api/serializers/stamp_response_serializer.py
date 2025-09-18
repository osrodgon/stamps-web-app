from rest_framework import serializers
from stamps_api.models import Stamp


class StampResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stamp
        fields = '__all__'