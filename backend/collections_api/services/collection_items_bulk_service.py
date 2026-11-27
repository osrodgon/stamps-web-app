"""Adding many stamps to a collection in one transaction (plan step C1).

The dialog of phase C adds one stamp, one series or a whole year, and none of
the three can be a loop of `POST items/`: a series of five would be five
requests, and a failure halfway would leave half of the set inside. This service
resolves the scope to the ids of the stamps, checks the cap, and inserts what is
missing with one `bulk_create`.

Three decisions live here:

- **Duplicates are skipped, not refused.** The single-item endpoint answers 409
to protect a copy that is there; this one exists to complete a set, so a stamp
already in the collection is counted as `skipped` and left untouched.
- **The copy is created with `collection` and `stamp` only.** Condition, price,
date, location and note are the user's to fill in later; `quantity` keeps the
model's default, and inventing values would write data nobody typed.
- **A cap, said out loud.** A year can resolve to thousands of stamps. Over
`MAX_STAMPS` the request fails with `TooMany` before writing anything, and the
screen asks the user to narrow it instead of doing half of it.
"""

from __future__ import annotations

from typing import List

from django.db import transaction

from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from stamps_api.models import Stamp


class CollectionItemsBulkService:
    """Adds the stamps a scope names to one collection, once each."""

    #: Most stamps one request may add. A year is the case that reaches it.
    MAX_STAMPS: int = 500

    class BulkAddError(Exception):
        """A scope that cannot be added as asked."""

    class NothingFound(BulkAddError):
        """The scope names no stamp of the catalogue."""

        def __init__(self, scope: str) -> None:
            """Keep the scope for the message the view logs."""
            self.scope = scope
            super().__init__(scope)

    class TooMany(BulkAddError):
        """The scope names more stamps than one request may add."""

        def __init__(self, total: int, limit: int) -> None:
            """Keep both numbers for the message the view answers."""
            self.total = total
            self.limit = limit
            super().__init__(f"{total} > {limit}")

    def add(self, collection: Collection, scope: str, data: dict) -> dict:
        """Add the stamps of one scope and answer what happened.

        Args:
            collection: the collection the copies go into; already the caller's.
            scope: `stamp`, `issue` or `year`.
            data: the validated body, with the key of the scope.

        Returns:
            `{"created": n, "skipped": n, "total": n}`, where `total` is what the
            scope resolved to.

        Raises:
            NothingFound: when the scope names no stamp.
            TooMany: when it names more than `MAX_STAMPS`.
        """
        with transaction.atomic():
            stamp_ids: List[int] = list(
                self.__stamps(scope, data).values_list("id", flat=True)
            )
            total = len(stamp_ids)

            if total == 0:
                raise CollectionItemsBulkService.NothingFound(scope)
            if total > self.MAX_STAMPS:
                raise CollectionItemsBulkService.TooMany(
                    total, self.MAX_STAMPS
                )

            owned = set(
                CollectionItem.objects.filter(
                    collection=collection, stamp_id__in=stamp_ids
                ).values_list("stamp_id", flat=True)
            )
            missing = [stamp_id for stamp_id in stamp_ids if stamp_id not in owned]

            CollectionItem.objects.bulk_create(
                [
                    CollectionItem(collection=collection, stamp_id=stamp_id)
                    for stamp_id in missing
                ],
                ignore_conflicts=True,
            )

            return {
                "created": len(missing),
                "skipped": total - len(missing),
                "total": total,
            }

    @staticmethod
    def __stamps(scope: str, data: dict):
        """The stamps the scope names, as a queryset of ids.

        Args:
            scope: `stamp`, `issue` or `year`; the serializer has checked it.
            data: the validated body.

        Returns:
            A `Stamp` queryset, not yet evaluated.
        """
        if scope == "stamp":
            return Stamp.objects.filter(pk__in=data["ids"])
        if scope == "issue":
            return Stamp.objects.filter(issue_id=data["issue"])
        return Stamp.objects.filter(issue__year__year=data["year"])
