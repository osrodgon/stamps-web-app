from rest_framework import serializers

class PaginationSerializer(serializers.Serializer):
    """
    Serializer for representing pagination details in item listing responses.

    Attributes:
        sort_by (str): The field to sort the items by.
        order (str): The order direction.
        page (int): The page number of the returned items.
        page_size (int): The number of items per page.
        total (int): The total number of items matching the query parameters.
        has_more (bool): Indicates if there are more items available beyond the current page.
    """
    sort_by = serializers.CharField(help_text="The field to sort the items by.")
    order = serializers.CharField(help_text="The order direction.")
    page = serializers.IntegerField(help_text="The page number of the returned items.")
    page_size = serializers.IntegerField(help_text="The number of items per page.")
    total = serializers.IntegerField(help_text="The total number of items matching the query parameters.")
    has_more = serializers.BooleanField(help_text="Indicates if there are more items available beyond the current page.")