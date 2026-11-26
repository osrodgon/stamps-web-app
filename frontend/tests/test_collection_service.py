"""Unit tests for services/collection_service.py.

The HTTP call is mocked: what matters here is the URL, the method, the JWT header
and the payload the service builds, plus the `None` it returns on a network error.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from core.urls import URLs
from services.collection_service import CollectionService

TOKEN = "header.payload.signature"


class ServiceTest:
    """Fixtures shared by the classes below."""

    @pytest.fixture
    def service(self) -> CollectionService:
        """A service with a token."""
        return CollectionService(TOKEN)

    @pytest.fixture
    def response(self) -> MagicMock:
        """A response the service can hand back untouched."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    @staticmethod
    def call_of(mock_request: AsyncMock) -> dict:
        """The keyword arguments of the single call the service made."""
        return mock_request.call_args[1]


class TestGetCollections(ServiceTest):
    """The list is a GET to the collections endpoint with the token."""

    async def test_it_calls_the_collections_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.get_collections()

        call = self.call_of(mock_request)
        assert result is response
        assert call["request_type"] == service.GET
        assert call["url"] == URLs.Backend.collections

    async def test_it_sends_the_jwt(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_collections()

        assert self.call_of(mock_request)["headers"] == {
            "Authorization": f"JWT {TOKEN}"
        }

    async def test_a_get_has_no_body(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_collections()

        assert "payload" not in self.call_of(mock_request)


class TestCreateCollection(ServiceTest):
    """Creating sends the name and nothing else."""

    async def test_it_posts_the_name(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.create_collection("My collection")

        call = self.call_of(mock_request)
        assert result is response
        assert call["request_type"] == service.POST
        assert call["url"] == URLs.Backend.collections
        assert call["payload"] == {"name": "My collection"}
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}


class TestUpdateCollection(ServiceTest):
    """Renaming is a PUT to the collection's own URL."""

    async def test_it_puts_the_name_to_the_collection_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.update_collection(7, "Renamed")

        call = self.call_of(mock_request)
        assert result is response
        assert call["request_type"] == service.PUT
        assert call["url"] == f"{URLs.Backend.collections}7"
        assert call["payload"] == {"name": "Renamed"}
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}

    async def test_the_id_has_no_trailing_slash(self, service, response):
        """The backend's route is `collections/<int:pk>`, without a slash."""
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.update_collection(12, "Renamed")

        assert self.call_of(mock_request)["url"] == f"{URLs.Backend.collections}12"


class TestDeleteCollection(ServiceTest):
    """Deleting is a DELETE to the collection's own URL, with no body."""

    async def test_it_deletes_the_collection_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.delete_collection(7)

        call = self.call_of(mock_request)
        assert result is response
        assert call["request_type"] == service.DELETE
        assert call["url"] == f"{URLs.Backend.collections}7"
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}
        assert "payload" not in call


class TestFailures(ServiceTest):
    """A network error is `None`, and the token belongs to the service."""

    async def test_a_network_error_is_none(self, service):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=None
        ):
            assert await service.get_collections() is None

    async def test_the_header_carries_this_services_token(self, response):
        other = CollectionService("another.token.here")

        with patch.object(
            other, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await other.get_collections()

        assert self.call_of(mock_request)["headers"] == {
            "Authorization": "JWT another.token.here"
        }
