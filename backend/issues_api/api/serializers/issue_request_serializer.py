from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from issues_api.models import Issue


class IssueRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = [
            'year',
            'date',
            'country',
            'name',
            'total_printed',
            'market_value',
            'number_owned',
            'stamp_type',
            'paper_type',
            'description',
            'location',
            'note',
            'perforation'
        ]
        extra_kwargs = {
            'extra': {'allow_extra_fields': False}
        }