"""The detail of one series of a collection (plan step B2).

The row is the stamp as the catalogue shows it — codes, face value, colours, catalogue
values — with the caller's copy under `item`, or `null` when they do not own it. The
stamp serializer is reused so the screen reads the same fields as the admin's cards.
"""

from typing import Optional

from rest_framework import serializers

from collection_items_api.models import CollectionItem
from condition_types_api.api.serializers.condition_type_response_serializer import (
    ConditionTypeResponseSerializer,
)
from issues_api.api.serializers.issue_response_serializer import (
    IssueResponseSerializer,
)
from locations_api.api.serializers.location_response_serializer import (
    LocationResponseSerializer,
)
from stamps_api.api.serializers.stamp_response_serializer import (
    StampResponseSerializer,
)


class CollectionItemDetailSerializer(serializers.ModelSerializer):
    """The user's copy, with the names of its condition and its location."""

    condition_type = ConditionTypeResponseSerializer(read_only=True)
    location = LocationResponseSerializer(read_only=True)

    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "condition_type",
            "location",
            "quantity",
            "price_paid",
            "acquisition_date",
            "note",
        ]


class CollectionStampSerializer(StampResponseSerializer):
    """One stamp of the series with the caller's item, or null."""

    item = serializers.SerializerMethodField()

    def get_item(self, stamp) -> Optional[dict]:
        """The item the service attached to the stamp, serialized."""
        item = getattr(stamp, "item", None)
        return CollectionItemDetailSerializer(item).data if item else None


class CollectionIssueFiguresSerializer(serializers.Serializer):
    """The three figures of the header: how many of the series are owned."""

    owned = serializers.IntegerField(
        help_text="How many stamps of the series the user owns."
    )
    total = serializers.IntegerField(help_text="How many stamps the series has.")
    paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
        required=False,
        help_text="Sum of the prices paid, or null when no price is kept.",
    )


class CollectionIssueDetailSerializer(serializers.Serializer):
    """The series, its stamps with the caller's copies and the summary."""

    issue = IssueResponseSerializer()
    stamps = CollectionStampSerializer(many=True)
    summary = CollectionIssueFiguresSerializer()
