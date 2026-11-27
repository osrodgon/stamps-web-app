from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from issues_api.models import Issue


class IssueRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    """
    Serializer for creating and updating Issue instances.

    This serializer handles the validation and deserialization of incoming
    data for creating or updating an issue.
    """
    class Meta:
        model = Issue
        fields = [
            'year',
            'date',
            'country',
            'name',
            'total_printed',
            'market_value_mnh',
            'market_value_used',
            'stamp_type',
            'print_type',
            'printer',
            'artist',
            'paper_type',
            'description',
            'note',
            'perforation'
        ]
        extra_kwargs = {
            'extra': {'allow_extra_fields': False}
        }
