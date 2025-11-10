from rest_framework import serializers

from paper_types_api.models import PaperType

class PaperTypeResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing PaperType instances in responses.

    This serializer formats the PaperType model data for client-facing
    responses.
    """
    class Meta:
        model = PaperType
        fields = ['id','name']
