"""Tests for the collection items endpoints, scoped to the JWT (plan step A1).

An item belongs to a collection, and a collection belongs to a user: the list only
returns the caller's items, an item can only be added to a collection of the
caller, and the update can touch the six fields of "Your copy" and nothing else.
"""

import pytest
from rest_framework import status

from _backend.settings import COLLECTION_ITEMS_URL_V1
from collection_items_api.api.serializers.collection_items_response_serializer import (
    CollectionItemsResponseSerializer,
)
from collection_items_api.models import CollectionItem
from common.api.messages import Messages
from common.core.jwt_token import JwtToken
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client  # noqa: F401  (fixture)
from common.test.collection_items_api_test_data import (
    collection_item_post_payload_ok,
    collection_item_put_payload_ok,
    collection_items_table,
)
from common.test.collections_api_test_data import collections_table
from common.test.colors_api_test_data import colors_table  # noqa: F401  (fixture)
from common.test.condition_types_api_test_data import condition_types_table
from common.test.countries_api_test_data import countries_table  # noqa: F401  (fixture)
from common.test.issues_api_test_data import issues_table  # noqa: F401  (fixture)
from common.test.locations_api_test_data import locations_table
from common.test.print_types_api_test_data import print_types_table  # noqa: F401  (fixture)
from common.test.stamp_types_api_test_data import stamp_types_table  # noqa: F401  (fixture)
from common.test.stamps_api_test_data import stamps_table
from common.test.users_api_test_data import users_table
from common.test.year_api_test_data import years_table  # noqa: F401  (fixture)
from users_api.models import UserCollection


class Api:
    """The endpoint and the headers these tests need, in one place."""

    @staticmethod
    def url(pk: int = None) -> str:
        """The collection items endpoint, optionally for one item."""
        base = f"/{COLLECTION_ITEMS_URL_V1}"
        return base if pk is None else f"{base}{pk}"

    @staticmethod
    def headers(user: UserCollection) -> dict:
        """A real Authorization header for `user`."""
        token = JwtToken().create(user)["token"]
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.fixture
def owner(users_table) -> dict:
    """Headers for the owner of the first collection."""
    return Api.headers(users_table[0])


@pytest.mark.django_db
class TestListItems(AbstractApiUnitTest):
    """The list is the caller's."""

    def test_it_returns_only_my_items(self, api_client, collection_items_table, owner):
        response = api_client.get(Api.url(), **owner)

        original = CollectionItemsResponseSerializer([collection_items_table[0]], many=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == original.data

    def test_another_users_item_is_not_listed(self, api_client, collection_items_table, owner):
        response = api_client.get(Api.url(), **owner)

        listed = {row["id"] for row in response.json()["data"]}

        assert collection_items_table[1].id not in listed

    def test_no_header_is_403(self, api_client):
        response = api_client.get(Api.url())

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["message"] == Messages.Auth.header_missing()

    def test_a_bad_token_is_403(self, api_client):
        response = api_client.get(Api.url(), HTTP_AUTHORIZATION="JWT not-a-token")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["message"] == Messages.Auth.invalid_jwt()

    def test_the_master_key_is_403(self, api_client):
        self.permission(granted=True)

        response = api_client.get(Api.url(), HTTP_AUTHORIZATION="API-KEY master")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["message"] == Messages.Auth.invalid_format()

    def test_a_database_error_is_500(self, api_client, owner):
        self.connection_lost(CollectionItem, "objects.filter")

        response = api_client.get(Api.url(), **owner)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["errors"][0]["message"] == Messages.Database.connection_lost()


@pytest.mark.django_db
class TestOneItem(AbstractApiUnitTest):
    """One item is mine or it does not exist."""

    def test_i_can_read_mine(self, api_client, collection_items_table, owner):
        response = api_client.get(Api.url(collection_items_table[0].id), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["note"] == collection_items_table[0].note

    def test_another_users_item_is_404(self, api_client, collection_items_table, owner):
        response = api_client.get(Api.url(collection_items_table[1].id), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["errors"][0]["message"] == Messages.Get.not_found(
            "collection item", collection_items_table[1].id
        )

    def test_a_missing_item_is_404(self, api_client, owner):
        response = api_client.get(Api.url(999), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAddCopy(AbstractApiUnitTest):
    """A copy goes into one of my collections."""

    def test_it_adds_the_item_to_my_collection(
        self, api_client, collections_table, collection_item_post_payload_ok, owner
    ):
        response = api_client.post(Api.url(), collection_item_post_payload_ok, format="json", **owner)

        assert response.status_code == status.HTTP_201_CREATED

        created = CollectionItem.objects.get(pk=response.json()["data"]["id"])
        assert created.collection_id == collections_table[0].id

    def test_adding_to_another_users_collection_is_404(
        self,
        api_client,
        collections_table,
        collection_items_table,
        collection_item_post_payload_ok,
        owner,
    ):
        # The pair already exists in the other user's collection: without the
        # ownership check the unique validator would answer 400, which tells the
        # caller that somebody holds that stamp there. It must be a 404.
        foreign = dict(
            collection_item_post_payload_ok, collection=collections_table[1].id
        )

        response = api_client.post(Api.url(), foreign, format="json", **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert CollectionItem.objects.filter(
            collection_id=collections_table[1].id,
            stamp_id=foreign["stamp"],
        ).count() == 1  # the other user's own item, nothing added

    def test_an_unknown_field_is_400(
        self, api_client, collection_item_post_payload_ok, owner
    ):
        payload = dict(collection_item_post_payload_ok, new_field="value")

        response = api_client.post(Api.url(), payload, format="json", **owner)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "new_field"


@pytest.mark.django_db
class TestUpdateCopy(AbstractApiUnitTest):
    """The update touches the six fields of "Your copy" and nothing else."""

    def test_i_can_update_my_copy(
        self, api_client, collection_items_table, collection_item_put_payload_ok, owner
    ):
        item = collection_items_table[0]

        response = api_client.put(
            Api.url(item.id), collection_item_put_payload_ok, format="json", **owner
        )

        assert response.status_code == status.HTTP_200_OK

        item.refresh_from_db()
        assert str(item.price_paid) == "1.75"
        assert item.note == collection_item_put_payload_ok["note"]

    def test_it_cannot_move_an_item_to_another_collection(
        self, api_client, collection_items_table, collections_table, owner
    ):
        item = collection_items_table[0]

        response = api_client.put(
            Api.url(item.id), {"collection": collections_table[1].id}, format="json", **owner
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "collection"

        item.refresh_from_db()
        assert item.collection_id == collections_table[0].id

    def test_it_cannot_change_the_stamp(
        self, api_client, collection_items_table, stamps_table, owner
    ):
        item = collection_items_table[0]

        response = api_client.put(
            Api.url(item.id), {"stamp": stamps_table[1].id}, format="json", **owner
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "stamp"

        item.refresh_from_db()
        assert item.stamp_id == stamps_table[0].id

    def test_updating_another_users_item_is_404(
        self, api_client, collection_items_table, collection_item_put_payload_ok, owner
    ):
        response = api_client.put(
            Api.url(collection_items_table[1].id),
            collection_item_put_payload_ok,
            format="json",
            **owner,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_i_can_remove_my_copy(self, api_client, collection_items_table, owner):
        response = api_client.delete(Api.url(collection_items_table[0].id), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert not CollectionItem.objects.filter(pk=collection_items_table[0].id).exists()

    def test_removing_another_users_item_is_404(
        self, api_client, collection_items_table, owner
    ):
        response = api_client.delete(Api.url(collection_items_table[1].id), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert CollectionItem.objects.filter(pk=collection_items_table[1].id).exists()
