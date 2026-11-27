from rest_framework import serializers
from common.api.serializers.pagination_serializer import PaginationSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer

class IssuePaginatedResponseSerializer(serializers.Serializer):
    """
    Serializer for representing a list of Issue instances along with pagination details.

    Attributes:
        issues (IssueResponseSerializer): List of issues matching the query parameters.
        pagination (PaginationSerializer): Pagination details for the current response.
    """
    issues = IssueResponseSerializer(many=True, help_text="List of issues matching the query parameters.")
    pagination = PaginationSerializer(help_text="Pagination details for the current response.")