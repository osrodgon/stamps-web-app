from rest_framework import serializers

from locations_api.models import Location

class LocationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id','name']
