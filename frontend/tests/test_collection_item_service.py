"""Unit tests for services/collection_item_service.py.

The HTTP call is mocked: what matters is the URL the service builds, the JWT header and
which filters travel in the query string.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from core.urls import URLs
from services.collection_item_service import CollectionItemService

TOKEN = "header.payload.signature"


class ServiceTest:
    """Fixtures shared by the classes below."""

    @pytest.fixture
    def service(self) -> CollectionItemService:
        """A service with a token."""
        return CollectionItemService(TOKEN)

    @pytest.fixture
    def response(self) -> MagicMock:
        """A response the service hands back untouched."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    @staticmethod
    def query(mock_request: AsyncMock) -> dict:
        """The query string of the single call the service made."""
        return parse_qs(urlparse(mock_request.call_args[1]["url"]).query)

    @staticmethod
    def call(mock_request: AsyncMock) -> dict:
        """The keyword arguments of the single call the service made."""
        return mock_request.call_args[1]


class TestGetSeries(ServiceTest):
    """The series of a collection live under the collection's URL."""

    async def test_it_calls_the_collection_issues_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.get_series(7)

        call = self.call(mock_request)
        assert result is response
        assert call["request_type"] == service.GET
        assert call["url"].startswith(f"{URLs.Backend.collections}7/issues/?")
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}

    async def test_the_default_parameters(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_series(7)

        assert self.query(mock_request) == {
            "page": ["1"],
            "pageSize": ["15"],
            "sortBy": ["date"],
            "order": ["asc"],
        }

    async def test_the_pagination_and_order_travel(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_series(
                7, page=3, page_size=30, sort_by="name", order="desc"
            )

        query = self.query(mock_request)
        assert query["page"] == ["3"]
        assert query["pageSize"] == ["30"]
        assert query["sortBy"] == ["name"]
        assert query["order"] == ["desc"]

    async def test_empty_filters_are_not_sent(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_series(7)

        query = self.query(mock_request)
        assert "name" not in query
        assert "year" not in query

    async def test_the_filters_travel_when_given(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.get_series(7, name="Isabel", year="1850-1860")

        query = self.query(mock_request)
        assert query["name"] == ["Isabel"]
        assert query["year"] == ["1850-1860"]

    async def test_a_network_error_is_none(self, service):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=None
        ):
            assert await service.get_series(7) is None
