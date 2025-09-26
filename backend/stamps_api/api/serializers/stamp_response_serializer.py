from turtle import color
from rest_framework import serializers
from stamps_api.models import Stamp


class StampResponseSerializer(serializers.ModelSerializer):
    issue = serializers.StringRelatedField()
    colors = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = Stamp
        fields = '__all__'