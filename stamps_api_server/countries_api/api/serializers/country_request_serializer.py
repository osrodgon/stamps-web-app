from rest_framework import serializers
from countries_api.models import Country

class CountryRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name']