"""Tests for the catalogue a collection can add from (plan step C2).

The point of the step is a page and a detail that do **not** ask for ownership, without
loosening the two screens that do: the first tests read what the dialog needs, the last
block proves B1 and B2 still hide what the collection does not hold.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collection_items_api.models import CollectionItem
from collections_api.services.collection_issue_detail_service import (
    CollectionIssueDetailService,
)
from collections_api.services.collection_issues_service import CollectionIssuesService
from common.core.jwt_token import JwtToken
from common.test.api_client import api_client  # noqa: F401  (fixture)
from common.test.collection_issues_test_data import (  # noqa: F401  (fixture)
    collection_issues_catalogue,
)
from common.test.collections_api_test_data import collections_table
from common.test.users_api_test_data import users_table
from issues_api.models import Issue
from users_api.models import UserCollection


pytestmark = pytest.mark.django_db


class Api:
    """The URLs and headers these tests need."""

    @staticmethod
    def catalogue(collection_id: int) -> str:
        """The page of the catalogue for a collection."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/catalogue/issues/"

    @staticmethod
    def detail(collection_id: int, issue_id: int) -> str:
        """One series of the catalogue for a collection."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/catalogue/issues/{issue_id}/"

    @staticmethod
    def headers(user: UserCollection) -> dict:
        """A real Authorization header for `user`."""
        token = JwtToken().create(user)["token"]
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.fixture
def owner(users_table) -> dict:
    """Headers for the user who owns the fixture's collection."""
    return Api.headers(users_table[0])


class Page:
    """Reading the rows of a page without depending on their order.

    The service hands the serializer `Issue` rows with the figures annotated, so the
    tests read attributes; the endpoint's JSON is the serializer's business.
    """

    @staticmethod
    def by_name(page: dict) -> dict:
        """The rows of the page, keyed by series name."""
        return {issue.name: issue for issue in page["issues"]}


class TestCataloguePage:
    """The page lists what the collection does not hold; B1 does not."""

    def test_a_series_the_collection_holds_nothing_of_appears(
        self, collection_issues_catalogue
    ):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], owned_only=False
        )

        assert "Nobody has this" in Page.by_name(page)

    def test_it_carries_the_three_figures_and_the_cover(
        self, collection_issues_catalogue
    ):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], owned_only=False
        )

        first = Page.by_name(page)["First series"]

        assert first.total_stamps == 2
        assert first.owned_stamps == 2
        assert first.paid == Decimal("10.00")
        assert first.catalogue_mnh == Decimal("30.00")
        assert first.cover_code == "F-A1"

    def test_a_series_nobody_owns_says_zero(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], owned_only=False
        )

        unowned = Page.by_name(page)["Nobody has this"]

        assert unowned.total_stamps == 1
        assert unowned.owned_stamps == 0
        assert unowned.paid is None

    def test_a_half_owned_series_counts_what_is_there(
        self, collection_issues_catalogue
    ):
        collection = collection_issues_catalogue["collection"]
        CollectionItem.objects.filter(
            collection=collection, stamp__issue=collection_issues_catalogue["first"]
        ).first().delete()

        page = CollectionIssuesService().page(collection, owned_only=False)

        assert Page.by_name(page)["First series"].owned_stamps == 1

    def test_a_series_without_stamps_is_not_a_row(self, collection_issues_catalogue):
        Issue.objects.create(
            year=collection_issues_catalogue["first"].year, name="Empty series"
        )

        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"], owned_only=False
        )

        assert "Empty series" not in Page.by_name(page)

    def test_the_name_filter_and_the_order_mirror_b1(
        self, collection_issues_catalogue
    ):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"],
            name="Nobody",
            sort_by="name",
            owned_only=False,
        )

        assert [issue.name for issue in page["issues"]] == ["Nobody has this"]

    def test_an_open_year_range_filters(self, collection_issues_catalogue):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"],
            year="1901-",
            owned_only=False,
        )

        assert page["pagination"]["total"] == 0

    def test_the_page_is_two_queries(
        self, collection_issues_catalogue, django_assert_num_queries
    ):
        with django_assert_num_queries(2):
            CollectionIssuesService().page(
                collection_issues_catalogue["collection"], owned_only=False
            )


class TestCatalogueDetail:
    """The detail reads any series, owned or not."""

    def test_a_series_the_collection_holds_nothing_of_is_read(
        self, collection_issues_catalogue
    ):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["nobody_has"].pk,
            owned_only=False,
        )

        assert [stamp.name for stamp in detail["stamps"]] == ["C1"]
        assert detail["stamps"][0].item is None
        assert detail["summary"] == {"owned": 0, "total": 1, "paid": None}

    def test_the_copies_are_marked_where_they_exist(self, collection_issues_catalogue):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["first"].pk,
            owned_only=False,
        )

        by_name = {stamp.name: stamp for stamp in detail["stamps"]}

        assert by_name["A1"].item is not None
        assert by_name["A2"].item is not None
        assert detail["summary"]["owned"] == 2

    def test_a_missing_series_is_none(self, collection_issues_catalogue):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"], 999, owned_only=False
        )

        assert detail is None

    def test_the_detail_is_four_queries(
        self, collection_issues_catalogue, django_assert_num_queries
    ):
        with django_assert_num_queries(4):
            CollectionIssueDetailService().for_collection(
                collection_issues_catalogue["collection"],
                collection_issues_catalogue["nobody_has"].pk,
                owned_only=False,
            )


class TestTheReadingScreensKeepTheirScope:
    """The new parameter must not loosen B1 or B2 by accident."""

    def test_b1_still_hides_what_the_collection_does_not_hold(
        self, collection_issues_catalogue
    ):
        page = CollectionIssuesService().page(
            collection_issues_catalogue["collection"]
        )

        assert "Nobody has this" not in Page.by_name(page)

    def test_b2_still_refuses_it(self, collection_issues_catalogue):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["nobody_has"].pk,
        )

        assert detail is None


class TestEndpoints:
    """The contract the dialog reads."""

    def test_the_page_answers_a_row_per_series(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.get(
            Api.catalogue(collection_issues_catalogue["collection"].pk), **owner
        )

        data = response.json()["data"]
        names = {issue["name"] for issue in data["issues"]}

        assert response.status_code == status.HTTP_200_OK
        assert "Nobody has this" in names
        assert data["pagination"]["total"] == 5

    def test_the_detail_answers_a_series_nobody_owns(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.get(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["nobody_has"].pk,
            ),
            **owner,
        )

        data = response.json()["data"]

        assert response.status_code == status.HTTP_200_OK
        assert data["summary"]["owned"] == 0
        assert data["stamps"][0]["item"] is None

    def test_a_missing_series_is_404(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.get(
            Api.detail(collection_issues_catalogue["collection"].pk, 999), **owner
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_foreign_collection_is_404(self, api_client, collections_table, owner):
        page = api_client.get(Api.catalogue(collections_table[1].pk), **owner)
        detail = api_client.get(
            Api.detail(collections_table[1].pk, collections_table[1].pk), **owner
        )

        assert page.status_code == status.HTTP_404_NOT_FOUND
        assert detail.status_code == status.HTTP_404_NOT_FOUND

    def test_without_a_token_it_is_403(self, api_client, collection_issues_catalogue):
        response = api_client.get(
            Api.catalogue(collection_issues_catalogue["collection"].pk)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
