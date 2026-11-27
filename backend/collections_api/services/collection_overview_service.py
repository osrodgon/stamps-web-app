"""The numbers and the covers behind the collections overview (plan steps A2, B3b).

A card needs four figures and a few pictures: how many series the collection
holds, how many stamps the user owns, how many stamps those series have in total
(the progress bar's denominator), what the copies cost so far, and up to twelve
stamps to build the collage.

The point of this class is the **cost**: the whole page is five queries, whatever
the number of cards. Doing it per card in the frontend would be an N+1 that grows
with the collection, and the covers would need a second round trip.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from django.db.models import Count, Sum

from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from stamps_api.models import Stamp
from users_api.models import UserCollection


class CollectionOverviewService:
    """Builds one row per collection, with its counters and its cover candidates."""

    #: Candidates the response carries. The frontend paints the first six whose
    #: picture file exists, so this is a batch, not a promise.
    MAX_COVERS = 12

    def for_user(self, user: UserCollection) -> List[dict]:
        """Return the overview rows of one user, ordered by collection name.

        Args:
            user: the user the JWT belongs to.

        Returns:
            One dict per collection with `id`, `name`, `series`, `stamps`, `total`,
            `paid` and `covers`; an empty list when the user has none.
        """
        collections = list(Collection.objects.filter(user=user).order_by("name"))
        if not collections:
            return []

        ids = [collection.pk for collection in collections]
        counts = self.__counts(ids)
        issues = self.__issues(ids)
        stamps_per_issue = self.__stamps_per_issue(issues)
        covers = self.__covers(ids)

        return [
            self.__row(collection, counts, issues, stamps_per_issue, covers)
            for collection in collections
        ]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def __counts(ids: List[int]) -> Dict[int, dict]:
        """Series, distinct stamps and money paid of each collection, in one query.

        `paid` is a `Sum` over the same rows the counters read, so a copy with a
        quantity of two still adds its price once — the quantity is a field of the
        item, not another row. It is `None` when no copy of the collection carries a
        price, which is not the same as having paid nothing.
        """
        rows = (
            CollectionItem.objects.filter(collection_id__in=ids)
            .values("collection_id")
            .annotate(
                series=Count("stamp__issue", distinct=True),
                stamps=Count("stamp", distinct=True),
                paid=Sum("price_paid"),
            )
        )
        return {row["collection_id"]: row for row in rows}

    @staticmethod
    def __issues(ids: List[int]) -> Dict[int, Set[int]]:
        """The distinct issue ids each collection touches, in one query."""
        grouped: Dict[int, Set[int]] = defaultdict(set)
        rows = (
            CollectionItem.objects.filter(collection_id__in=ids)
            .values_list("collection_id", "stamp__issue_id")
            .distinct()
        )
        for collection_id, issue_id in rows:
            grouped[collection_id].add(issue_id)
        return grouped

    @staticmethod
    def __stamps_per_issue(issues: Dict[int, Set[int]]) -> Dict[int, int]:
        """How many stamps each of those issues has, in one grouped query."""
        issue_ids = set().union(*issues.values()) if issues else set()
        if not issue_ids:
            return {}

        rows = (
            Stamp.objects.filter(issue_id__in=issue_ids)
            .values("issue_id")
            .annotate(total=Count("id"))
        )
        return {row["issue_id"]: row["total"] for row in rows}

    def __covers(self, ids: List[int]) -> Dict[int, List[dict]]:
        """The first `MAX_COVERS` stamps with a picture code, in one query.

        Only stamps with a `fesofi_code` can become a picture: the frontend
        resolves `assets/stamps/<year>/<code>.webp`, and an empty code has no file.
        The order is stable (year, date, id) so a card does not shuffle between
        loads.
        """
        covers: Dict[int, List[dict]] = defaultdict(list)
        rows = (
            CollectionItem.objects.filter(
                collection_id__in=ids,
                stamp__fesofi_code__isnull=False,
            )
            .exclude(stamp__fesofi_code="")
            .order_by(
                "collection_id",
                "stamp__issue__year__year",
                "stamp__issue__date",
                "stamp_id",
            )
            .values_list(
                "collection_id", "stamp__issue__year__year", "stamp__fesofi_code"
            )
        )
        for collection_id, year, code in rows:
            if len(covers[collection_id]) < self.MAX_COVERS:
                covers[collection_id].append({"year": year, "code": code})
        return covers

    # ------------------------------------------------------------------
    # Shaping
    # ------------------------------------------------------------------

    @staticmethod
    def __row(
        collection: Collection,
        counts: Dict[int, dict],
        issues: Dict[int, Set[int]],
        stamps_per_issue: Dict[int, int],
        covers: Dict[int, List[dict]],
    ) -> dict:
        """One collection with its figures and its covers."""
        counted = counts.get(collection.pk, {})
        total = sum(
            stamps_per_issue.get(issue_id, 0)
            for issue_id in issues.get(collection.pk, ())
        )
        return {
            "id": collection.pk,
            "name": collection.name,
            "series": counted.get("series", 0),
            "stamps": counted.get("stamps", 0),
            "total": total,
            "paid": counted.get("paid"),
            "covers": covers.get(collection.pk, []),
        }
