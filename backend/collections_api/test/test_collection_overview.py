"""Tests for the overview counters and covers (plan step A2).

They call the service directly: the figures are its job, and counting them here
keeps the endpoint tests about the contract. The query count is pinned because the
whole point of the step is that a page of cards costs a fixed number of queries.
"""

import pytest

from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from collections_api.services.collection_overview_service import CollectionOverviewService
from common.test.collection_overview_test_data import overview_catalogue  # noqa: F401
from common.test.collections_api_test_data import collections_table
from common.test.users_api_test_data import users_table
from stamps_api.models import Stamp


pytestmark = pytest.mark.django_db


class Rows:
    """Reading the overview rows without depending on their order."""

    @staticmethod
    def of(rows: list, collection_id: int) -> dict:
        """The row of one collection."""
        return next(row for row in rows if row["id"] == collection_id)


class TestCounters:
    """`series`, `stamps` and `total` answer three different questions."""

    def test_series_counts_distinct_series(self, overview_catalogue):
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(rows, overview_catalogue["collection"].pk)["series"] == 2

    def test_stamps_counts_distinct_stamps(self, overview_catalogue):
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(rows, overview_catalogue["collection"].pk)["stamps"] == 2

    def test_a_quantity_does_not_inflate_the_count(self, overview_catalogue):
        """One of the two items holds two copies; the card still says two stamps."""
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(rows, overview_catalogue["collection"].pk)["stamps"] == 2

    def test_total_counts_the_stamps_of_those_series(self, overview_catalogue):
        """Two stamps in each of the two series, one of them not owned."""
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(rows, overview_catalogue["collection"].pk)["total"] == 4

    def test_an_empty_collection_is_all_zeroes(self, overview_catalogue, collections_table):
        empty = collections_table[2]

        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(rows, empty.pk) == {
            "id": empty.pk,
            "name": empty.name,
            "series": 0,
            "stamps": 0,
            "total": 0,
            "covers": [],
        }

    def test_another_users_items_do_not_count(self, overview_catalogue, users_table):
        """What user 2 owns is counted for user 2 and for nobody else."""
        theirs = Collection.objects.create(user=users_table[1], name="Theirs")
        CollectionItem.objects.create(
            collection=theirs, stamp=overview_catalogue["other"]
        )

        their_rows = CollectionOverviewService().for_user(users_table[1])
        my_rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert Rows.of(their_rows, theirs.pk)["stamps"] == 1
        assert Rows.of(my_rows, overview_catalogue["collection"].pk)["stamps"] == 2

    def test_a_collection_without_an_owner_is_not_listed(self, overview_catalogue):
        Collection.objects.create(name="Nobody", user=None)

        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert "Nobody" not in {row["name"] for row in rows}


class TestCovers:
    """Only stamps with a picture code, at most twelve, always the same."""

    def test_only_the_stamps_with_a_code_are_covers(self, overview_catalogue):
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        covers = Rows.of(rows, overview_catalogue["collection"].pk)["covers"]

        assert covers == [
            {"year": overview_catalogue["year"], "code": "F-OWNED"}
        ]

    def test_a_stamp_without_a_code_contributes_nothing(self, overview_catalogue):
        rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        covers = Rows.of(rows, overview_catalogue["collection"].pk)["covers"]

        assert len(covers) == 1

    def test_the_covers_are_stable(self, overview_catalogue):
        first = CollectionOverviewService().for_user(overview_catalogue["user"])
        second = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert first == second

    def test_the_covers_are_capped_at_twelve(self, overview_catalogue, users_table):
        collection = Collection.objects.create(user=users_table[0], name="Many")
        for index in range(13):
            stamp = Stamp.objects.create(
                issue=overview_catalogue["first_issue"],
                name=f"Stamp {index}",
                face_value="1",
                fesofi_code=f"F-{index}",
            )
            CollectionItem.objects.create(collection=collection, stamp=stamp)

        rows = CollectionOverviewService().for_user(users_table[0])

        assert len(Rows.of(rows, collection.pk)["covers"]) == 12


class TestQueryCount:
    """The page costs five queries whatever the number of cards."""

    def test_the_overview_is_five_queries(self, overview_catalogue, django_assert_num_queries):
        with django_assert_num_queries(5):
            rows = CollectionOverviewService().for_user(overview_catalogue["user"])

        assert len(rows) == 2
