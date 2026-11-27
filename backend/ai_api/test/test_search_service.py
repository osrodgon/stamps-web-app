"""Tests for the series locator (plan step A6 first slice + A2 errors).

`SearchService.find_series_url` asks the Fesofi catalogue first and falls back to
the search engine, so the exact-name problem disappears for the catalogue and the
search backend stays as a second door.
"""

from unittest.mock import Mock, patch

import pytest

from ai_api.services import search_service as search_module
from ai_api.services.search_service import SearchService
from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceUnavailable,
)


class FakeResponse:
    """Minimal stand-in for an httpx response."""

    def __init__(self, status_code: int = 200, payload=None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class FakeClient:
    """Records what the service asks the network for."""

    def __init__(self, response=None, error=None) -> None:
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.response


@pytest.fixture(autouse=True)
def serper_configured(monkeypatch):
    """Give the fallback a URL and a key unless a test removes them."""
    monkeypatch.setattr(search_module, "SERPER_URL", "https://google.serper.dev/search")
    monkeypatch.setattr(search_module, "SERPER_API_KEY", "test-key")


def catalogue_returning(urls):
    """Patch the Fesofi catalogue with a fixed answer."""
    stub = Mock()
    stub.find_product_urls.return_value = urls
    return patch.object(search_module, "FesofiCatalogue", return_value=stub), stub


class TestCatalogueFirst:
    """The catalogue answers by attribute, so it goes first."""

    def test_the_catalogue_url_wins(self):
        patch_catalogue, catalogue = catalogue_returning(
            ["https://catalogodesellos.fesofi.es/producto/2884/"]
        )
        client = FakeClient()

        with patch_catalogue:
            url = SearchService(client=client).find_series_url("navidad", "1986")

        assert url == "https://catalogodesellos.fesofi.es/producto/2884/"
        assert client.calls == []
        catalogue.find_product_urls.assert_called_once_with("navidad", "1986")

    def test_the_search_engine_is_used_when_the_catalogue_has_nothing(self):
        patch_catalogue, _ = catalogue_returning([])
        client = FakeClient(
            FakeResponse(200, {"organic": [
                {"link": "https://elsewhere.test/x"},
                {"link": "https://catalogodesellos.fesofi.es/producto/0199/"},
            ]})
        )

        with patch_catalogue:
            url = SearchService(client=client).find_series_url("Castillos", "2007")

        assert url == "https://catalogodesellos.fesofi.es/producto/0199/"
        assert len(client.calls) == 1

    def test_a_broken_catalogue_falls_back_instead_of_failing(self):
        stub = Mock()
        stub.find_product_urls.side_effect = SourceUnavailable("down")
        client = FakeClient(
            FakeResponse(200, {"organic": [
                {"link": "https://catalogodesellos.fesofi.es/producto/0199/"},
            ]})
        )

        with patch.object(search_module, "FesofiCatalogue", return_value=stub):
            url = SearchService(client=client).find_series_url("Castillos", "2007")

        assert url == "https://catalogodesellos.fesofi.es/producto/0199/"


class TestSearchErrors:
    """A failure to ask is not "there is nothing"."""

    def test_no_configuration_is_a_configuration_error(self, monkeypatch):
        monkeypatch.setattr(search_module, "SERPER_URL", None)
        monkeypatch.setattr(search_module, "SERPER_API_KEY", None)

        with catalogue_returning([])[0]:
            with pytest.raises(SourceConfigurationError):
                SearchService(client=FakeClient()).find_series_url("Navidad", "1986")

    def test_a_refused_key_is_a_configuration_error(self):
        client = FakeClient(FakeResponse(403))

        with catalogue_returning([])[0]:
            with pytest.raises(SourceConfigurationError):
                SearchService(client=client).find_series_url("Navidad", "1986")

    def test_a_server_error_is_unavailable(self):
        client = FakeClient(FakeResponse(503))

        with catalogue_returning([])[0]:
            with pytest.raises(SourceUnavailable):
                SearchService(client=client).find_series_url("Navidad", "1986")

    def test_no_product_link_means_none(self):
        client = FakeClient(FakeResponse(200, {"organic": [{"link": "https://elsewhere.test"}]}))

        with catalogue_returning([])[0]:
            assert SearchService(client=client).find_series_url("Navidad", "1986") is None
