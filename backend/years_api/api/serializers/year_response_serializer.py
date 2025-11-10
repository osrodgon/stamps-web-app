from rest_framework import serializers
from years_api.models import Year


class YearResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing Year instances in responses.

    This serializer formats the Year model data for client-facing
    responses.
    """
    class Meta:
        model = Year
        fields = ['id', 'year']