"""Tests for the series detail and the item writes (plan step B2).

The service test pins the figures and the cost; the endpoint tests pin the contract the
third screen reads. The item writes were scoped in A1 and only their response shape is
checked here.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from _backend.settings import COLLECTION_ITEMS_URL_V1, COLLECTIONS_URL_V1
from collection_items_api.models import CollectionItem
from collections_api.services.collection_issue_detail_service import (
    CollectionIssueDetailService,
)
from common.api.messages import Messages
from common.core.jwt_token import JwtToken
from common.test.api_client import api_client  # noqa: F401  (fixture)
from common.test.collection_issues_test_data import (  # noqa: F401  (fixture)
    collection_issues_catalogue,
)
from common.test.collections_api_test_data import collections_table
from common.test.condition_types_api_test_data import condition_types_table
from common.test.locations_api_test_data import locations_table
from common.test.users_api_test_data import users_table
from stamps_api.models import Stamp
from users_api.models import UserCollection


pytestmark = pytest.mark.django_db


class Api:
    """The URLs and headers these tests need."""

    @staticmethod
    def detail(collection_id: int, issue_id: int) -> str:
        """The series detail endpoint."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/issues/{issue_id}/"

    @staticmethod
    def items(collection_id: int) -> str:
        """The endpoint that adds a copy."""
        return f"/{COLLECTIONS_URL_V1}{collection_id}/items/"

    @staticmethod
    def item(item_id: int) -> str:
        """One collection item."""
        return f"/{COLLECTION_ITEMS_URL_V1}{item_id}"

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
    """A stamp of the first series the user does not own."""
    return Stamp.objects.create(
        issue=collection_issues_catalogue["first"],
        name="A3",
        face_value="1",
        fesofi_code="F-A3",
    )


class TestDetailService:
    """Every stamp of the series, with the caller's item or null."""

    def test_stamps_and_items(self, collection_issues_catalogue, unowned_stamp):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["first"].id,
        )

        by_name = {stamp.name: stamp for stamp in detail["stamps"]}

        assert len(detail["stamps"]) == 3
        assert by_name["A1"].item is not None
        assert by_name["A3"].item is None

    def test_the_summary(self, collection_issues_catalogue, unowned_stamp):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["first"].id,
        )

        assert detail["summary"] == {
            "owned": 2,
            "total": 3,
            "paid": Decimal("10.00"),
        }

    def test_a_series_the_collection_does_not_hold(self, collection_issues_catalogue):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["nobody_has"].id,
        )

        assert detail is None

    def test_a_missing_series(self, collection_issues_catalogue):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"], 999
        )

        assert detail is None

    def test_the_detail_is_five_queries(
        self, collection_issues_catalogue, django_assert_num_queries
    ):
        """The issue, its stamps, their colours, the copies and the neighbours.

        The four of B2 plus the one the arrows cost, which is why the catalogue
        reader — no list behind it — does not ask for them.
        """
        with django_assert_num_queries(5):
            CollectionIssueDetailService().for_collection(
                collection_issues_catalogue["collection"],
                collection_issues_catalogue["first"].id,
            )


class TestDetailEndpoint:
    """The contract the third screen reads."""

    def test_the_series_and_its_stamps(
        self, api_client, collection_issues_catalogue, unowned_stamp, owner
    ):
        response = api_client.get(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["first"].pk,
            ),
            **owner,
        )

        data = response.json()["data"]
        by_name = {stamp["name"]: stamp for stamp in data["stamps"]}

        assert response.status_code == status.HTTP_200_OK
        assert data["issue"]["name"] == "First series"
        assert by_name["A1"]["item"] is not None
        assert by_name["A3"]["item"] is None
        assert data["summary"]["owned"] == 2
        assert data["summary"]["total"] == 3

    def test_the_item_carries_the_names(
        self,
        api_client,
        collection_issues_catalogue,
        condition_types_table,
        locations_table,
        owner,
    ):
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"],
            stamp__name="A1",
        )
        item.condition_type = condition_types_table[0]
        item.location = locations_table[0]
        item.save()

        response = api_client.get(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["first"].pk,
            ),
            **owner,
        )

        rows = response.json()["data"]["stamps"]
        a1 = next(row for row in rows if row["name"] == "A1")

        assert a1["item"]["condition_type"]["name"] == condition_types_table[0].name
        assert a1["item"]["location"]["name"] == locations_table[0].name

    def test_another_users_collection_is_404(
        self, api_client, collections_table, owner
    ):
        response = api_client.get(
            Api.detail(collections_table[1].pk, collections_table[1].pk), **owner
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_series_the_collection_does_not_hold_is_404(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.get(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["nobody_has"].pk,
            ),
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["errors"][0]["message"] == Messages.Get.not_found(
            "issue", collection_issues_catalogue["nobody_has"].pk
        )


class TestNeighbours:
    """The arrows of the detail walk the collection's list, in its order."""

    def test_the_first_series_has_a_next_and_no_previous(
        self, collection_issues_catalogue
    ):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["first"].pk,
        )

        assert detail["neighbours"] == {
            "position": 1,
            "total": 4,
            "previous": None,
            "next": collection_issues_catalogue["second"].pk,
        }

    def test_the_last_series_has_a_previous_and_no_next(
        self, collection_issues_catalogue
    ):
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["no_picture"].pk,
        )

        assert detail["neighbours"]["position"] == 4
        assert detail["neighbours"]["next"] is None
        assert detail["neighbours"]["previous"] == collection_issues_catalogue[
            "aardvark"
        ].pk

    def test_the_catalogue_reader_has_no_neighbours(
        self, collection_issues_catalogue
    ):
        """There is no list behind the dialog, so it is told so."""
        detail = CollectionIssueDetailService().for_collection(
            collection_issues_catalogue["collection"],
            collection_issues_catalogue["first"].pk,
            owned_only=False,
        )

        assert detail["neighbours"] is None

    def test_the_arrows_travel_in_the_response(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.get(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["first"].pk,
            ),
            **owner,
        )

        neighbours = response.json()["data"]["neighbours"]

        assert neighbours["total"] == 4
        assert neighbours["next"] == collection_issues_catalogue["second"].pk


class TestRemoveSeries:
    """Removing a series from a collection deletes the copies, not the catalogue."""

    def test_it_deletes_the_copies_of_the_series(
        self, api_client, collection_issues_catalogue, owner
    ):
        collection = collection_issues_catalogue["collection"]
        issue = collection_issues_catalogue["first"]

        response = api_client.delete(Api.detail(collection.pk, issue.pk), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {"deleted": 2}
        assert CollectionItem.objects.filter(
            collection=collection, stamp__issue=issue
        ).count() == 0
        assert Stamp.objects.filter(issue=issue).count() == 2

    def test_a_series_the_collection_does_not_hold_is_404(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.delete(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["nobody_has"].pk,
            ),
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_foreign_collection_is_404(self, api_client, collections_table, owner):
        response = api_client.delete(
            Api.detail(collections_table[1].pk, collections_table[1].pk), **owner
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_without_a_token_it_is_403(
        self, api_client, collection_issues_catalogue
    ):
        response = api_client.delete(
            Api.detail(
                collection_issues_catalogue["collection"].pk,
                collection_issues_catalogue["first"].pk,
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddCopy:
    """A copy is added once; adding it again is a conflict, not an overwrite."""

    def test_it_adds_to_my_collection(
        self, api_client, collection_issues_catalogue, owner
    ):
        stamp = Stamp.objects.get(issue=collection_issues_catalogue["nobody_has"])

        response = api_client.post(
            Api.items(collection_issues_catalogue["collection"].pk),
            {"stamp": stamp.pk},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["condition_type"] is None
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"], stamp=stamp
        )
        # A copy is at least one stamp.
        assert item.quantity == 1

    def test_a_stamp_already_there_is_409(
        self, api_client, collection_issues_catalogue, owner
    ):
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"],
            stamp__name="A1",
        )
        item.note = "keep me"
        item.save()

        response = api_client.post(
            Api.items(collection_issues_catalogue["collection"].pk),
            {"stamp": item.stamp_id},
            format="json",
            **owner,
        )

        item.refresh_from_db()
        assert response.status_code == status.HTTP_409_CONFLICT
        assert item.note == "keep me"

    def test_another_users_collection_is_404(
        self, api_client, collections_table, collection_issues_catalogue, owner
    ):
        stamp = Stamp.objects.first()

        response = api_client.post(
            Api.items(collections_table[1].pk),
            {"stamp": stamp.pk},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_missing_stamp_is_404(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.post(
            Api.items(collection_issues_catalogue["collection"].pk),
            {"stamp": 999999},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_payload_without_a_stamp_is_400(
        self, api_client, collection_issues_catalogue, owner
    ):
        response = api_client.post(
            Api.items(collection_issues_catalogue["collection"].pk),
            {},
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "stamp"


class TestItemWrites:
    """The write endpoints A1 scoped answer with the names the screen reads."""

    def test_update_returns_the_names(
        self,
        api_client,
        collection_issues_catalogue,
        condition_types_table,
        locations_table,
        owner,
    ):
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"],
            stamp__name="A1",
        )

        response = api_client.put(
            Api.item(item.pk),
            {
                "condition_type": condition_types_table[0].pk,
                "location": locations_table[0].pk,
                "quantity": 3,
            },
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["condition_type"]["name"] == (
            condition_types_table[0].name
        )
        assert response.json()["data"]["location"]["name"] == locations_table[0].name
        assert response.json()["data"]["quantity"] == 3

    def test_delete_removes_the_copy(
        self, api_client, collection_issues_catalogue, owner
    ):
        item = CollectionItem.objects.get(
            collection=collection_issues_catalogue["collection"],
            stamp__name="A1",
        )

        response = api_client.delete(Api.item(item.pk), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert not CollectionItem.objects.filter(pk=item.pk).exists()
