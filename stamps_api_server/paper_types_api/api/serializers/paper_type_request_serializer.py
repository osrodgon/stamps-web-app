from rest_framework import serializers

from paper_types_api.models import PaperType

class PaperTypeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperType
        fields = ['name']
        
    def to_internal_value(self, data):
        # Check for unexpected fields
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )
        return super().to_internal_value(data)