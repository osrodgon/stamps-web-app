from rest_framework import serializers
from issues_api.models import Issue


class IssueResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing Issue instances in responses.

    This serializer formats the Issue model data for client-facing responses,
    including string representations of related fields for better readability.
    """
    country = serializers.StringRelatedField()
    year = serializers.StringRelatedField()
    location = serializers.StringRelatedField(allow_null=True)
    stamp_type = serializers.StringRelatedField(allow_null=True)
    paper_type = serializers.StringRelatedField(allow_null=True)

    class Meta:
        model = Issue
        fields = '__all__'