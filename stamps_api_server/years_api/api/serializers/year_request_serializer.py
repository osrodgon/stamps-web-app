from rest_framework import serializers
from years_api.models import Year

class YearRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ['year']