"""Unit tests for services/catalogue_service.py (plan step C3).

The HTTP call is mocked: what matters is the URL, the method, the JWT header and the
body each scope sends. The service hands the response back untouched, so a 400 or a
404 is the page's to read.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from core.urls import URLs
from services.catalogue_service import CatalogueService

TOKEN = "header.payload.signature"


class ServiceTest:
    """Fixtures shared by the classes below."""

    @pytest.fixture
    def service(self) -> CatalogueService:
        """A service with a token."""
        return CatalogueService(TOKEN)

    @pytest.fixture
    def response(self) -> MagicMock:
        """A response the service hands back untouched."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        return response

    @staticmethod
    def call(mock_request: AsyncMock) -> dict:
        """The keyword arguments of the single call the service made."""
        return mock_request.call_args[1]

    @staticmethod
    def query(mock_request: AsyncMock) -> dict:
        """The query string of the single call the service made."""
        return parse_qs(urlparse(mock_request.call_args[1]["url"]).query)


class TestSearch(ServiceTest):
    """The page of the catalogue mirrors the collection's own list."""

    async def test_it_calls_the_catalogue_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.search_issues(7)

        call = self.call(mock_request)

        assert result is response
        assert call["request_type"] == service.GET
        assert call["url"].startswith(
            f"{URLs.Backend.collections}7/catalogue/issues/?"
        )
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}

    async def test_the_default_parameters(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.search_issues(7)

        assert self.query(mock_request) == {
            "page": ["1"],
            "pageSize": ["15"],
            "sortBy": ["date"],
            "order": ["asc"],
        }

    async def test_the_filters_travel_when_they_are_set(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.search_issues(
                7, page=2, page_size=30, name="Isabel", year="1852"
            )

        query = self.query(mock_request)

        assert query["page"] == ["2"]
        assert query["pageSize"] == ["30"]
        assert query["name"] == ["Isabel"]
        assert query["year"] == ["1852"]

    async def test_an_empty_filter_stays_out_of_the_query(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.search_issues(7, name="", year="")

        assert "name" not in self.query(mock_request)
        assert "year" not in self.query(mock_request)


class TestDetail(ServiceTest):
    """One series of the catalogue, with or without copies."""

    async def test_it_calls_the_catalogue_detail_url(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.get_issue(7, 42)

        call = self.call(mock_request)

        assert result is response
        assert call["request_type"] == service.GET
        assert call["url"] == (
            f"{URLs.Backend.collections}7/catalogue/issues/42/"
        )
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}


class TestAdds(ServiceTest):
    """The three scopes differ only in the body; the endpoint is one."""

    async def test_adding_stamps_sends_its_ids(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            result = await service.add_stamps(7, [10, 11])

        call = self.call(mock_request)

        assert result is response
        assert call["request_type"] == service.POST
        assert call["url"] == f"{URLs.Backend.collections}7/items/bulk/"
        assert call["payload"] == {"scope": "stamp", "ids": [10, 11]}
        assert call["headers"] == {"Authorization": f"JWT {TOKEN}"}

    async def test_adding_a_series_sends_its_id(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.add_issue(7, 42)

        call = self.call(mock_request)

        assert call["request_type"] == service.POST
        assert call["url"] == f"{URLs.Backend.collections}7/items/bulk/"
        assert call["payload"] == {"scope": "issue", "issue": 42}

    async def test_adding_a_year_sends_the_year(self, service, response):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=response
        ) as mock_request:
            await service.add_year(7, 1852)

        call = self.call(mock_request)

        assert call["request_type"] == service.POST
        assert call["payload"] == {"scope": "year", "year": 1852}


class TestAnswers(ServiceTest):
    """Nothing is swallowed: the page decides what a 400 or a 403 means."""

    async def test_a_refusal_comes_back_untouched(self, service):
        refused = MagicMock(spec=requests.Response)
        refused.status_code = 400

        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=refused
        ):
            result = await service.add_year(7, 1852)

        assert result is refused
        assert result.status_code == 400

    async def test_a_network_error_is_none(self, service):
        with patch.object(
            service, "_make_request", new_callable=AsyncMock, return_value=None
        ):
            assert await service.search_issues(7) is None


class TestNoFlet:
    """The service is Flet-free, as every service in the app is."""

    def test_the_module_imports_no_flet(self):
        source = inspect.getsource(CatalogueService)

        assert "flet" not in source
