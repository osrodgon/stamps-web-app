from rest_framework import serializers
from years_api.models import Year


class YearResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ['id', 'year']