"""Tests for the series of a collection (plan step B1).

They call the service for the figures and the endpoint for the contract: the figures
are the step's job, and the endpoint has to keep `/issues/`'s shape so the frontend
reuses its pagination.
"""

from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collection_items_api.models import CollectionItem
from collections_api.services.collection_issues_service import (
    CollectionIssuesService,
)
from common.api.messages import Messages
from common.core.jwt_token import JwtToken
from common.test.api_client import api_client  # noqa: F401  (fixture)
from common.test.collection_issues_test_data import (  # noqa: F401  (fixture)
    collection_issues_catalogue,
)
from common.test.collections_api_test_data import collections_table
from common.test.users_api_test_data import users_table
from issues_api.models import Issue
from stamps_api.models import Stamp
from users_api.models import UserCollection


pytestmark = pytest.mark.django_db


class Api:
    """The endpoint and the headers these tests need."""

    @staticmethod
    def url(collection_id: int) -> str:
        """The series endpoint of one collection."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/issues/"

    @staticmethod
    def headers(user: UserCollection) -> dict:
        """A real Authorization header for `user`."""
        token = JwtToken().create(user)["token"]
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.fixture
def owner(users_table) -> dict:
    """Headers for the user who owns the fixture's collection."""
    return Api.headers(users_table[0])


class Rows:
    """Reading the page without depending on the order."""

    @staticmethod
    def series(rows: list, issue_id: int):
        """The series (a model instance) with that id, from the service."""
        return next(issue for issue in rows if issue.id == issue_id)

    @staticmethod
    def serialized(rows: list, issue_id: int) -> dict:
        """The same row once the serializer has shaped it."""
        return next(row for row in rows if row["id"] == issue_id)


class TestSeriesList:
    """Only the series the user holds something of, with their figures."""

    def test_only_series_with_items_are_listed(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        ids = {issue.id for issue in page["issues"]}
        assert collection_issues_catalogue["nobody_has"].id not in ids
        assert len(ids) == 4

    def test_the_three_figures_of_a_series(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["first"].id)

        assert row.total_stamps == 2
        assert row.owned_stamps == 2
        assert row.paid == Decimal("10.00")

    def test_a_quantity_does_not_count_twice(self, collection_issues_catalogue):
        """A1 holds two copies; the series owns two stamps, not three."""
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["first"].id)

        assert row.owned_stamps == 2

    def test_the_catalogue_value_of_the_series(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["first"].id)

        assert row.catalogue_mnh == Decimal("30.00")

    def test_the_cover_is_a_stamp_with_a_code(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["first"].id)

        assert row.cover_code == "F-A1"

    def test_a_series_without_codes_has_no_cover(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["no_picture"].id)

        assert row.cover_code is None

    def test_a_series_without_prices_has_no_paid(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        row = Rows.series(page["issues"], collection_issues_catalogue["no_picture"].id)

        assert row.paid is None
        assert row.catalogue_mnh is None


class TestOrder:
    """The order `/issues/` uses: the chosen column, then the id."""

    def test_the_default_order_is_date_ascending(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(collection_issues_catalogue["collection"])

        dates = [issue.date for issue in page["issues"]]

        assert dates == sorted(dates)

    def test_descending_order(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], order="desc"
        )

        dates = [issue.date for issue in page["issues"]]

        assert dates == sorted(dates, reverse=True)

    def test_sort_by_name(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], sort_by="name"
        )

        names = [issue.name for issue in page["issues"]]

        assert names == sorted(names)

    def test_an_unknown_sort_falls_back_to_date(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], sort_by="nonsense"
        )

        assert page["pagination"]["sort_by"] == "date"


class TestFilters:
    """The same name and year filters as the issues list."""

    def test_the_name_filter(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], name="Second"
        )

        assert [issue.name for issue in page["issues"]] == ["Second series"]

    def test_the_year_filter(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], year="1899"
        )

        assert page["issues"] == []
        assert page["pagination"]["total"] == 0

    def test_the_year_range_filter(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], year="1899-1900"
        )

        assert page["pagination"]["total"] == 4


class TestPagination:
    """15 per page by default, with the block `/issues/` returns."""

    def test_the_first_page_and_the_block(self, collection_issues_catalogue):
        collection = collection_issues_catalogue["collection"]
        year = collection_issues_catalogue["first"].year
        for index in range(17):
            issue = Issue.objects.create(
                year=year, name=f"Filler {index}", date=date(1900, 6, 1)
            )
            stamp = Stamp.objects.create(
                issue=issue, name=f"F{index}", face_value="1", fesofi_code=f"FF{index}"
            )
            CollectionItem.objects.create(collection=collection, stamp=stamp)

        page = CollectionIssuesService().page(collection)

        assert len(page["issues"]) == 15
        assert page["pagination"] == {
            "sort_by": "date",
            "order": "asc",
            "page": 1,
            "page_size": 15,
            "total": 21,
            "has_more": True,
        }

    def test_the_last_page(self, collection_issues_catalogue):
        collection = collection_issues_catalogue["collection"]
        year = collection_issues_catalogue["first"].year
        for index in range(17):
            issue = Issue.objects.create(
                year=year, name=f"Filler {index}", date=date(1900, 6, 1)
            )
            stamp = Stamp.objects.create(
                issue=issue, name=f"F{index}", face_value="1", fesofi_code=f"FF{index}"
            )
            CollectionItem.objects.create(collection=collection, stamp=stamp)

        page = CollectionIssuesService().page(collection, page=2)

        assert len(page["issues"]) == 6
        assert page["pagination"]["has_more"] is False

    def test_a_page_size_of_zero_returns_all(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], page_size=0
        )

        assert len(page["issues"]) == 4
        assert page["pagination"]["page_size"] == 4
        assert page["pagination"]["has_more"] is False


class TestQueryCount:
    """The page costs two queries: the count and the rows."""

    def test_two_queries(self, collection_issues_catalogue, django_assert_num_queries):
        with django_assert_num_queries(2):
            page = CollectionIssuesService().page(
                collection_issues_catalogue["collection"]
            )

        assert len(page["issues"]) == 4


class TestEndpoint:
    """The endpoint keeps the shape and the ownership."""

    def test_it_returns_the_page(self, api_client, collection_issues_catalogue, owner):
        response = api_client.get(
            Api.url(collection_issues_catalogue["collection"].pk), **owner
        )

        data = response.json()["data"]
        row = Rows.serialized(data["issues"], collection_issues_catalogue["first"].id)

        assert response.status_code == status.HTTP_200_OK
        assert set(row) == {
            "id",
            "year",
            "date",
            "name",
            "country",
            "stamp_type",
            "cover",
            "total_stamps",
            "owned_stamps",
            "paid",
            "catalogue_mnh",
        }
        assert row["cover"] == {"year": 1900, "code": "F-A1"}
        assert row["paid"] == "10.00"
        assert data["pagination"]["total"] == 4

    def test_another_users_collection_is_404(
        self, api_client, collections_table, owner
    ):
        response = api_client.get(Api.url(collections_table[1].pk), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["errors"][0]["message"] == Messages.Get.not_found(
            "collection", collections_table[1].pk
        )

    def test_no_header_is_403(self, api_client, collection_issues_catalogue):
        response = api_client.get(
            Api.url(collection_issues_catalogue["collection"].pk)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
