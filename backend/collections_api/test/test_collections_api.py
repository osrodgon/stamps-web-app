"""Tests for the collections endpoints, scoped to the JWT (plan step A1).

The point of the step is ownership: a user only ever sees and edits their own
collections, a foreign row is a 404, a missing header is a 401, and a bad token or
the master key is a 403. The tokens are real (`JwtToken().create()`), so these
tests exercise the authentication and permission classes instead of mocking them.
"""

import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collections_api.models import Collection
from common.api.messages import Messages
from common.core.jwt_token import JwtToken
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client  # noqa: F401  (fixture)
from common.test.collection_overview_test_data import overview_catalogue  # noqa: F401  (fixture)
from common.test.collections_api_test_data import (
    collections_table,
    collection_post_payload_ok,
    collection_put_payload_ok,
)
from common.test.users_api_test_data import users_table
from users_api.models import UserCollection


class Api:
    """The endpoint and the headers these tests need, in one place."""

    @staticmethod
    def url(pk: int = None) -> str:
        """The collections endpoint, optionally for one collection."""
        base = f"/{COLLECTIONS_URL_V1}"
        return base if pk is None else f"{base}{pk}"

    @staticmethod
    def headers(user: UserCollection) -> dict:
        """A real Authorization header for `user`."""
        token = JwtToken().create(user)["token"]
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.fixture
def owner(users_table) -> dict:
    """Headers for the user who owns collections 1 and 3 of the fixture."""
    return Api.headers(users_table[0])


@pytest.fixture
def other(users_table) -> dict:
    """Headers for the user who owns collection 2."""
    return Api.headers(users_table[1])


@pytest.mark.django_db
class TestListCollections(AbstractApiUnitTest):
    """The list is the caller's, ordered by name."""

    def test_it_returns_only_my_collections(self, api_client, collections_table, users_table, owner):
        response = api_client.get(Api.url(), **owner)

        mine = {collections_table[0].id, collections_table[2].id}
        data = response.json()["data"]

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert {row["id"] for row in data} == mine
        assert len(data) == 2
        assert all(
            set(row) == {"id", "name", "series", "stamps", "total", "covers"}
            for row in data
        )

    def test_the_list_is_ordered_by_name(self, api_client, owner):
        response = api_client.get(Api.url(), **owner)

        names = [row["name"] for row in response.json()["data"]]

        assert names == sorted(names)

    def test_a_card_carries_its_counters_and_covers(
        self, api_client, overview_catalogue, owner
    ):
        response = api_client.get(Api.url(), **owner)

        row = next(
            row
            for row in response.json()["data"]
            if row["id"] == overview_catalogue["collection"].pk
        )

        assert row["series"] == 2
        assert row["stamps"] == 2
        assert row["total"] == 4
        assert row["covers"] == [
            {"year": overview_catalogue["year"], "code": "F-OWNED"}
        ]

    def test_another_users_collection_is_not_listed(self, api_client, collections_table, users_table, owner):
        response = api_client.get(Api.url(), **owner)

        listed = {row["id"] for row in response.json()["data"]}

        assert collections_table[1].id not in listed

    def test_a_user_without_collections_gets_an_empty_list(self, api_client, users_table):
        stranger = UserCollection.objects.create(
            username="stranger",
            email="stranger@example.com",
            password_hash="hash",
            first_name="Stra",
            last_name="Nger",
        )

        response = api_client.get(Api.url(), **Api.headers(stranger))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == []

    def test_no_header_is_403(self, api_client):
        response = api_client.get(Api.url())

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["message"] == Messages.Auth.header_missing()
        assert response.json()["errors"][0]["code"] == Messages.Code.authentication_failed()

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
        self.connection_lost(Collection, "objects.filter")

        response = api_client.get(Api.url(), **owner)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["errors"][0]["message"] == Messages.Database.connection_lost()


@pytest.mark.django_db
class TestOneCollection(AbstractApiUnitTest):
    """One collection is mine or it does not exist."""

    def test_i_can_read_mine(self, api_client, collections_table, owner):
        response = api_client.get(Api.url(collections_table[0].id), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["name"] == collections_table[0].name

    def test_another_users_collection_is_404(self, api_client, collections_table, owner):
        response = api_client.get(Api.url(collections_table[1].id), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["errors"][0]["message"] == Messages.Get.not_found(
            "collection", collections_table[1].id
        )

    def test_a_missing_collection_is_404(self, api_client, owner):
        response = api_client.get(Api.url(999), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_i_can_rename_mine(self, api_client, collections_table, collection_put_payload_ok, owner):
        response = api_client.put(
            Api.url(collections_table[0].id), collection_put_payload_ok, format="json", **owner
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["name"] == collection_put_payload_ok["name"]
        assert Collection.objects.get(pk=collections_table[0].id).name == (
            collection_put_payload_ok["name"]
        )

    def test_renaming_another_users_collection_is_404(
        self, api_client, collections_table, collection_put_payload_ok, owner
    ):
        response = api_client.put(
            Api.url(collections_table[1].id), collection_put_payload_ok, format="json", **owner
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Collection.objects.get(pk=collections_table[1].id).name == collections_table[1].name

    def test_i_can_delete_mine(self, api_client, collections_table, owner):
        response = api_client.delete(Api.url(collections_table[0].id), **owner)

        assert response.status_code == status.HTTP_200_OK
        assert not Collection.objects.filter(pk=collections_table[0].id).exists()

    def test_deleting_another_users_collection_is_404(self, api_client, collections_table, owner):
        response = api_client.delete(Api.url(collections_table[1].id), **owner)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Collection.objects.filter(pk=collections_table[1].id).exists()


@pytest.mark.django_db
class TestCreateCollection(AbstractApiUnitTest):
    """A new collection belongs to the user of the token."""

    def test_it_creates_for_the_token_user(
        self, api_client, collections_table, users_table, collection_post_payload_ok, owner
    ):
        payload = dict(collection_post_payload_ok, user=users_table[1].id)

        response = api_client.post(Api.url(), payload, format="json", **owner)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["name"] == payload["name"]
        assert response.json()["data"]["user"]["id"] == users_table[0].id

        created = Collection.objects.get(name=payload["name"])
        assert created.user_id == users_table[0].id

    def test_a_missing_name_is_400(self, api_client, collection_post_payload_ok, owner):
        payload = dict(collection_post_payload_ok)
        del payload["name"]

        response = api_client.post(Api.url(), payload, format="json", **owner)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "name"

    def test_an_unknown_field_is_400(self, api_client, collection_post_payload_ok, owner):
        payload = dict(collection_post_payload_ok, new_field="value")

        response = api_client.post(Api.url(), payload, format="json", **owner)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"][0]["field"] == "new_field"

    def test_creating_without_a_header_is_403(self, api_client, collection_post_payload_ok):
        response = api_client.post(Api.url(), collection_post_payload_ok, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCollectionModel:
    """The model still names its owner and its name."""

    def test_str_representation(self, users_table):
        collection = Collection.objects.create(name="Mine", user=users_table[0])

        assert str(collection) == f"{users_table[0].username} - Mine"
