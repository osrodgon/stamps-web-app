from rest_framework import serializers
from common.api.serializers.pagination_serializer import PaginationSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer

class IssuePaginatedResponseSerializer(serializers.Serializer):
    """
    Serializer for representing a list of Issue instances along with pagination details.
    
    This serializer combines the IssueDataSerializer for the main data payload with 
    the IssuePaginationSerializer to provide a comprehensive response structure for issue listings.
    """
    issues = IssueResponseSerializer(many=True, help_text="List of issues matching the query parameters.")
    pagination = PaginationSerializer(help_text="Pagination details for the current response.")