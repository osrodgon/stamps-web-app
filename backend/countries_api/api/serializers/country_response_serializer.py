from rest_framework import serializers
from countries_api.models import Country

class CountryResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']