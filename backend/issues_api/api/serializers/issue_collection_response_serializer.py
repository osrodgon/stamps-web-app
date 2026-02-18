from rest_framework import serializers

class IssueCollectionResponseSerializer(serializers.Serializer):
    # Issue-level fields
    issue_name = serializers.CharField(
        required=True
    )
    issue_date = serializers.DateField(
        required=False, 
        allow_null=True
    )