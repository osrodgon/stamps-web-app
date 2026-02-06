from rest_framework import serializers

class PaginationSerializer(serializers.Serializer):
    """
    Serializer for representing pagination details in issue listing responses.
    
    This serializer defines the structure for pagination metadata included in responses that 
    return lists of issues. It provides fields for the page number, page size, total number of matching issues, 
    and a flag indicating if more issues are available beyond the current page.
    """
    sort_by = serializers.CharField(help_text="The field to sort the issues by.")
    order = serializers.CharField(help_text="The order direction.")
    page = serializers.IntegerField(help_text="The page number of the returned issues.")
    page_size = serializers.IntegerField(help_text="The number of issues per page.")
    total = serializers.IntegerField(help_text="The total number of issues matching the query parameters.")
    has_more = serializers.BooleanField(help_text="Indicates if there are more issues available beyond the current page.")