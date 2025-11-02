from rest_framework import serializers
from countries_api.models import Country

class CountryResponseSerializer(serializers.ModelSerializer):
    """Serializes `Country` data for API responses.

    This serializer is designed for read operations to format `Country`
    instances for output, providing a simple representation of the country
    including its ID and name.
    """
    class Meta:
        model = Country
        fields = ['id', 'name']