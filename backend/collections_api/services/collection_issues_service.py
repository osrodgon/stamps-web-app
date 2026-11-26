"""The series of one collection, paginated (plan step B1).

The second screen needs the series a collection holds, with three figures per row:
how many stamps the series has, how many the user owns and what that is worth. The
endpoint mirrors `/issues/` — same parameters, same defaults, same pagination
block — but filtered to the series where the user holds something.

The cost is the point: two queries, the `count()` and one annotated page, whatever the
page size. The collection's figures travel as subqueries so the stamps join is not
multiplied by the items of other users.
"""

from __future__ import annotations

from typing import Dict

from django.db import connection
from django.db.models import (
    CharField,
    Count,
    DecimalField,
    Exists,
    F,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce

from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from issues_api.models import Issue
from stamps_api.models import Stamp


class CollectionIssuesService:
    """Builds one page of the series of a collection."""

    #: Series per page when the caller does not say.
    DEFAULT_PAGE_SIZE: int = 15
    #: The columns the screen can order by.
    SORT_FIELDS: tuple = ("date", "name")

    def page(
        self,
        collection: Collection,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        name: str = "",
        year: str = "",
        sort_by: str = "date",
        order: str = "asc",
    ) -> Dict[str, object]:
        """Return one page of the series of `collection`.

        Args:
            collection: the collection, already checked to belong to the caller.
            page: 1-based page number.
            page_size: rows per page; 0 means all of them.
            name: filter by series name.
            year: a year or a `start-end` range.
            sort_by: `date` or `name`.
            order: `asc` or `desc`.

        Returns:
            `{"issues": [...], "pagination": {...}}`, the shape the serializer and
            `TablePagination` expect.
        """
        sort_by, order = self.__normalise(sort_by, order)
        page = max(1, page)
        page_size = max(0, page_size)

        issues = self.__ordered(
            self.__filtered(self.__queryset(collection), name, year),
            sort_by,
            order,
        )
        total = issues.count()

        if page_size > 0:
            start = (page - 1) * page_size
            rows = list(issues[start:start + page_size])
        else:
            start = 0
            rows = list(issues)
            page_size = total

        return {
            "issues": rows,
            "pagination": {
                "sort_by": sort_by,
                "order": order,
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": page_size > 0 and (start + page_size) < total,
            },
        }

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @staticmethod
    def __queryset(collection: Collection) -> QuerySet:
        """The series of the collection, with its three figures and its cover."""
        owned = CollectionItem.objects.filter(
            collection=collection, stamp__issue=OuterRef("pk")
        )
        paid = (
            CollectionItem.objects.filter(
                collection=collection, stamp__issue=OuterRef("pk")
            )
            .values("stamp__issue")
            .annotate(value=Sum("price_paid"))
            .values("value")[:1]
        )
        owned_stamps = (
            CollectionItem.objects.filter(
                collection=collection, stamp__issue=OuterRef("pk")
            )
            .values("stamp__issue")
            .annotate(value=Count("stamp", distinct=True))
            .values("value")[:1]
        )
        cover = (
            Stamp.objects.filter(issue=OuterRef("pk"), fesofi_code__isnull=False)
            .exclude(fesofi_code="")
            .order_by("id")
            .values("fesofi_code")[:1]
        )

        return (
            Issue.objects.filter(Exists(owned))
            .select_related("year", "country", "stamp_type")
            .annotate(
                total_stamps=Count("stamps", distinct=True),
                catalogue_mnh=Sum("stamps__market_value_mnh"),
                owned_stamps=Coalesce(
                    Subquery(owned_stamps, output_field=IntegerField()), 0
                ),
                paid=Subquery(
                    paid,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                cover_code=Subquery(cover, output_field=CharField()),
            )
        )

    @staticmethod
    def __filtered(issues: QuerySet, name: str, year: str) -> QuerySet:
        """Apply the name and year filters the issues list also understands."""
        if name:
            lookup = (
                "name__unaccent__icontains"
                if connection.vendor == "postgresql"
                else "name__icontains"
            )
            issues = issues.filter(**{lookup: name})

        if year:
            try:
                if "-" in year:
                    start, end = year.split("-", 1)
                    issues = issues.filter(year__year__range=(int(start), int(end)))
                else:
                    issues = issues.filter(year__year=int(year))
            except (TypeError, ValueError):
                pass

        return issues

    def __ordered(self, issues: QuerySet, sort_by: str, order: str) -> QuerySet:
        """Order by the chosen column, nulls last, with the id as the last key."""
        field = F("name") if sort_by == "name" else F("date")
        if order == "desc":
            return issues.order_by(field.desc(nulls_last=True), "-id")
        return issues.order_by(field.asc(nulls_last=True), "id")

    def __normalise(self, sort_by: str, order: str) -> tuple:
        """Keep the order total even when the caller sends something else."""
        if sort_by not in self.SORT_FIELDS:
            sort_by = "date"
        if order not in ("asc", "desc"):
            order = "asc"
        return sort_by, order
