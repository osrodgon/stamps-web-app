"""The shape of the series of one collection (plan step B1).

The rows come from `CollectionIssuesService` with annotations already computed, so the
serializer reads them as the contract names them: the figures of the collection and the
catalogue fields the card shows.
"""

from typing import Optional

from rest_framework import serializers

from common.api.serializers.pagination_serializer import PaginationSerializer


class CollectionIssueCoverSerializer(serializers.Serializer):
    """The stamp whose picture is the series' thumbnail."""

    year = serializers.IntegerField(
        help_text="Emission year, half of the picture's path."
    )
    code = serializers.CharField(
        help_text="Fesofi code, the file name of the picture."
    )


class CollectionIssueSummarySerializer(serializers.Serializer):
    """One series of a collection, as the second screen reads it."""

    id = serializers.IntegerField(help_text="The series' id.")
    year = serializers.IntegerField(
        source="year.year", help_text="The emission year."
    )
    date = serializers.DateField(
        allow_null=True, help_text="The emission date, or null."
    )
    name = serializers.CharField(help_text="The series' name.")
    country = serializers.CharField(
        source="country.name", allow_null=True, required=False
    )
    stamp_type = serializers.CharField(
        source="stamp_type.name", allow_null=True, required=False
    )
    cover = serializers.SerializerMethodField()
    total_stamps = serializers.IntegerField(
        help_text="How many stamps the series has."
    )
    owned_stamps = serializers.IntegerField(
        help_text="How many of them the user owns; copies do not count twice."
    )
    paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
        required=False,
        help_text="What the user paid for their copies, or null when no price is kept.",
    )
    catalogue_mnh = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
        required=False,
        help_text="Sum of the catalogue values of the series' stamps, or null.",
    )

    def get_cover(self, issue) -> Optional[dict]:
        """The cover the card can paint, or null when no stamp has a code."""
        code = getattr(issue, "cover_code", None)
        if not code:
            return None
        return {"year": issue.year.year, "code": code}


class CollectionIssuePageSerializer(serializers.Serializer):
    """One page of series with the pagination block `/issues/` already uses."""

    issues = CollectionIssueSummarySerializer(many=True)
    pagination = PaginationSerializer()
