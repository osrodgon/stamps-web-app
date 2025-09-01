from rest_framework import serializers

from config_api.models import Config


class ConfigRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['property', 'value']
        
    def to_internal_value(self, data):
        # Check for unexpected fields
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )
        return super().to_internal_value(data)