"""Tests for the bulk add of collection items (plan step C1).

The service tests pin the three scopes, the numbers and the fact that a copy
already there is left as it was; the endpoint tests pin the contract the dialog of
phase C reads.
"""

import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collection_items_api.models import CollectionItem
from collections_api.services.collection_items_bulk_service import (
    CollectionItemsBulkService,
)
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
from years_api.models import Year


pytestmark = pytest.mark.django_db


class Api:
    """The URL and the headers these tests need."""

    @staticmethod
    def bulk(collection_id: int) -> str:
        """The endpoint that adds many stamps."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/items/bulk/"

    @staticmethod
    def headers(user: UserCollection) -> dict:
        """A real Authorization header for `user`."""
        token = JwtToken().create(user)["token"]
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.fixture
def owner(users_table) -> dict:
    """Headers for the user who owns the fixture's collection."""
    return Api.headers(users_table[0])


@pytest.fixture
def unowned_stamp(collection_issues_catalogue) -> Stamp:
    """The only stamp of a series the user holds nothing of."""
    return Stamp.objects.get(issue=collection_issues_catalogue["nobody_has"])


class Service:
    """Calls the service with the fixture's collection."""

    @staticmethod
    def add(catalogue: dict, scope: str, **data) -> dict:
        """Add one scope and return the answer."""
        return CollectionItemsBulkService().add(
            catalogue["collection"], scope, {"scope": scope, **data}
        )


class TestScopes:
    """One stamp, one series or one year: three ways of naming the same thing."""

    def test_the_ids_of_some_stamps(self, collection_issues_catalogue, unowned_stamp):
        result = Service.add(
            collection_issues_catalogue, "stamp", ids=[unowned_stamp.pk]
        )

        assert result == {"created": 1, "skipped": 0, "total": 1}
        assert CollectionItem.objects.filter(
            collection=collection_issues_catalogue["collection"], stamp=unowned_stamp
        ).exists()

    def test_a_whole_series(self, collection_issues_catalogue):
        """The first series has two stamps and the user holds both."""
        result = Service.add(
            collection_issues_catalogue,
            "issue",
            issue=collection_issues_catalogue["first"].pk,
        )

        assert result == {"created": 0, "skipped": 2, "total": 2}

    def test_a_whole_year(self, collection_issues_catalogue):
        """Six stamps of 1900; five were already there, one was not."""
        result = Service.add(
            collection_issues_catalogue,
            "year",
            year=collection_issues_catalogue["year"],
        )

        assert result == {"created": 1, "skipped": 5, "total": 6}

    def test_a_stamp_already_there_is_skipped(self, collection_issues_catalogue):
        owned = CollectionItem.objects.filter(
            collection=collection_issues_catalogue["collection"]
        ).first()

        result = Service.add(
            collection_issues_catalogue, "stamp", ids=[owned.stamp_id]
        )

        assert result == {"created": 0, "skipped": 1, "total": 1}
        assert CollectionItem.objects.filter(
            collection=collection_issues_catalogue["collection"]
        ).count() == 5

    def test_repeating_it_creates_nothing(
        self, collection_issues_catalogue, unowned_stamp
    ):
        assert Service.add(
            collection_issues_catalogue, "stamp", ids=[unowned_stamp.pk]
        )["created"] == 1
        again = Service.add(
            collection_issues_catalogue, "stamp", ids=[unowned_stamp.pk]
        )

        assert again == {"created": 0, "skipped": 1, "total": 1}

    def test_the_copies_that_were_there_are_not_touched(
        self, collection_issues_catalogue
    ):
        """A1 is held with quantity 2 and 7.50 paid; adding its year changes nothing."""
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"], stamp__name="A1"
        )

        Service.add(
            collection_issues_catalogue,
            "year",
            year=collection_issues_catalogue["year"],
        )

        item.refresh_from_db()
        assert item.quantity == 2
        assert str(item.price_paid) == "7.50"

    def test_a_new_copy_carries_only_the_collection_and_the_stamp(
        self, collection_issues_catalogue, unowned_stamp
    ):
        Service.add(collection_issues_catalogue, "stamp", ids=[unowned_stamp.pk])

        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"], stamp=unowned_stamp
        )

        assert item.condition_type is None
        assert item.location is None
        assert item.price_paid is None
        assert item.acquisition_date is None
        assert item.note is None
        assert item.quantity is None


class TestRefusals:
    """What the service refuses, and that it writes nothing when it says no."""

    def test_a_scope_that_names_no_stamp(self, collection_issues_catalogue):
        with pytest.raises(CollectionItemsBulkService.NothingFound):
            Service.add(collection_issues_catalogue, "year", year=1)

    def test_more_than_the_cap_writes_nothing(self, collection_issues_catalogue):
        year = Year.objects.create(year=1899)
        issue = Issue.objects.create(year=year, name="Huge")
        Stamp.objects.bulk_create(
            [
                Stamp(issue=issue, name=f"S{index}", face_value="1")
                for index in range(501)
            ]
        )

        with pytest.raises(CollectionItemsBulkService.TooMany) as refused:
            Service.add(collection_issues_catalogue, "year", year=1899)

        assert refused.value.total == 501
        assert refused.value.limit == 500
        assert CollectionItem.objects.filter(
            collection=collection_issues_catalogue["collection"], stamp__issue=issue
        ).count() == 0

    def test_the_cost_is_three_queries_and_its_savepoint(
        self, collection_issues_catalogue, unowned_stamp, django_assert_num_queries
    ):
        """The ids, what is already there, the insert, and the savepoint pair.

        The three statements do not grow with the scope; the two savepoints are
        what `transaction.atomic()` costs to make the counts and the insert one
        decision.
        """
        with django_assert_num_queries(5):
            Service.add(
                collection_issues_catalogue, "stamp", ids=[unowned_stamp.pk]
            )


class TestEndpoint:
    """The contract the dialog reads."""

    def test_it_answers_the_three_numbers(
        self, api_client, collection_issues_catalogue, unowned_stamp, owner
    ):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "stamp", "ids": [unowned_stamp.pk]},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"] == {"created": 1, "skipped": 0, "total": 1}

    def test_an_unknown_scope_is_400(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "everything"},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_a_missing_key_is_400(self, api_client, collection_issues_catalogue, owner):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "issue"},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_the_key_of_another_scope_is_400(
        self, api_client, collection_issues_catalogue, unowned_stamp, owner
    ):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={
                "scope": "issue",
                "issue": collection_issues_catalogue["first"].pk,
                "ids": [unowned_stamp.pk],
            },
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_a_year_without_stamps_is_404(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "year", "year": 1},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_foreign_collection_is_404(self, api_client, collections_table, owner):
        response = api_client.post(
            Api.bulk(collections_table[1].pk),
            data={"scope": "year", "year": 1900},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_without_a_token_it_is_403(self, api_client, collection_issues_catalogue):
        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "year", "year": 1900},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_the_cap_answers_400_with_the_number(
        self, api_client, collection_issues_catalogue, owner
    ):
        year = Year.objects.create(year=1898)
        issue = Issue.objects.create(year=year, name="Huge")
        Stamp.objects.bulk_create(
            [
                Stamp(issue=issue, name=f"L{index}", face_value="1")
                for index in range(501)
            ]
        )

        response = api_client.post(
            Api.bulk(collection_issues_catalogue["collection"].pk),
            data={"scope": "year", "year": 1898},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "501" in str(response.json()["errors"])
