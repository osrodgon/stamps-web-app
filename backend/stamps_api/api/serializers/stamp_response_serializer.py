from rest_framework import serializers
from stamps_api.models import Stamp


class StampResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for representing Stamp instances in responses.

    This serializer formats the Stamp model data for client-facing responses,
    including string representations of related fields like 'issue' and 'colors'
    for better readability.
    """
    issue = serializers.StringRelatedField()
    colors = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = Stamp
        # `updated_at` is internal bookkeeping for DataDesk: keeping it out of the
        # response leaves the public payload and the OpenAPI schema unchanged.
        exclude = ["updated_at"]