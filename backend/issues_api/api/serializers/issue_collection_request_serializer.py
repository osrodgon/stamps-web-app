from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer


class IssueCollectionRequestSerializer(GenericSerializer, serializers.Serializer):
    # Issue-level fields
    issue_name = serializers.CharField(
        required=True
    )
    description = serializers.CharField(
        allow_blank=True, 
        required=False, 
        default="n/a"
    )
    issue_date = serializers.DateField(
        required=False, 
        allow_null=True
    )
    artist = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    printer = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    print_type = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    perforation = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    paper_type = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    stamp_type = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    notes = serializers.CharField(
        allow_blank=True, 
        allow_null=True, 
        required=False, 
        default="n/a"
    )
    total_printed = serializers.IntegerField(
        allow_null=True, 
        required=False
    )
    market_value_mnh = serializers.FloatField(
        allow_null=True, 
        required=False
    )
    market_value_used = serializers.FloatField(
        allow_null=True, 
        required=False
    )
    
    # Stamps list
    stamps = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
