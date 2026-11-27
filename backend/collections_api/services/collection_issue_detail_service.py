"""One series of a collection with its stamps and the caller's copies (plan step B2).

The third screen shows the series as the catalogue has it, read-only, and under each
stamp the user's copy when they own it. This service loads the three pieces — the
issue, its stamps and the caller's items — and attaches each item to its stamp, so the
serializer reads a flat row.

Queries: the issue, its stamps, their colours (the serializer shows them) and the
caller's items. Four, whatever the number of stamps.
"""

from __future__ import annotations

from django.db import transaction

from decimal import Decimal
from typing import Optional

from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from collections_api.services.collection_issues_service import (
    CollectionIssuesService,
)
from issues_api.models import Issue
from stamps_api.models import Stamp


class CollectionIssueDetailService:
    """Builds the detail of one series of one collection."""

    def for_collection(
        self,
        collection: Collection,
        issue_id: int,
        owned_only: bool = True,
    ) -> Optional[dict]:
        """Return the issue, its stamps with the caller's items and the summary.

        Args:
            collection: the collection, already checked to belong to the caller.
            issue_id: the series to read.
            owned_only: `True` to refuse a series the collection holds nothing of,
                which is what the reading screen needs; `False` to read any series
                of the catalogue, which is what the dialog that adds stamps needs
                (plan step C2).

        Returns:
            `{"issue", "stamps", "summary"}`, or None when the series does not exist
            or — with `owned_only` — the collection holds nothing of it.
        """
        issue = (
            Issue.objects.select_related(
                "year",
                "country",
                "stamp_type",
                "print_type",
                "printer",
                "artist",
                "paper_type",
            )
            .filter(pk=issue_id)
            .first()
        )
        if issue is None:
            return None

        items = {
            item.stamp_id: item
            for item in CollectionItem.objects.filter(
                collection=collection, stamp__issue=issue
            ).select_related("condition_type", "location")
        }
        if not items and owned_only:
            # A series the collection holds nothing of is not part of it.
            return None

        stamps = list(
            Stamp.objects.filter(issue=issue)
            .prefetch_related("colors")
            .order_by("id")
        )
        for stamp in stamps:
            stamp.item = items.get(stamp.id)

        return {
            "issue": issue,
            "stamps": stamps,
            "summary": self.__summary(stamps, items),
            # The arrows of the detail walk the collection's list, so they only
            # exist when the collection is the one holding the series: the
            # catalogue reader (the dialog) has no list behind it.
            "neighbours": (
                CollectionIssuesService().neighbours(collection, issue.pk)
                if owned_only
                else None
            ),
        }

    def remove(self, collection: Collection, issue_id: int) -> Optional[int]:
        """Delete the caller's copies of one series from their collection.

        It removes what the collection holds, never the catalogue: the series and
        its stamps stay in the database for everybody else. One transaction, and
        the count it returns is the number of copies that went.

        Args:
            collection: the collection, already checked to belong to the caller.
            issue_id: the series whose copies are removed.

        Returns:
            How many copies were deleted, or None when the collection held none.
        """
        with transaction.atomic():
            items = CollectionItem.objects.filter(
                collection=collection, stamp__issue_id=issue_id
            )
            count = items.count()
            if count == 0:
                return None
            items.delete()
            return count

    @staticmethod
    def __summary(stamps: list, items: dict) -> dict:
        """The three figures the header shows: owned, total and paid."""
        prices = [
            item.price_paid
            for item in items.values()
            if item.price_paid is not None
        ]
        return {
            "owned": len(items),
            "total": len(stamps),
            "paid": sum(prices, Decimal("0")) if prices else None,
        }
