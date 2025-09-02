from rest_framework import serializers

from locations_api.models import Location

class LocationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['name']
        
    def to_internal_value(self, data):
        # Check for unexpected fields
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )
        return super().to_internal_value(data)
