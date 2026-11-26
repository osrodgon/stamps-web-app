"""Tests for the price source that reads the search (plan step A7).

An asking price inside a snippet, with the condition guessed from the wording. A
result without a price is skipped: a missing price is not a price of zero.
"""

from decimal import Decimal

import httpx
import pytest

from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceUnavailable,
)
from ai_api.sources.http import HttpClient
from ai_api.sources.search_prices import SearchPrices


def search(results, status_code=200) -> SearchPrices:
    """A price source over a fake search backend."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"organic": results})

    client = HttpClient(
        allowed_hosts=["todocoleccion.net", "ebay.es", "google.serper.dev"],
        transport=httpx.MockTransport(handler),
        cache_ttl=0,
    )
    return SearchPrices(
        client=client, url="https://google.serper.dev/search", key="test-key"
    )


def result(link, title="", snippet="", price=None):
    """One organic result, the way the search returns it."""
    text = snippet if price is None else f"{snippet} {price}"
    return {"link": link, "title": title, "snippet": text}


class TestPrices:
    """Only allowlisted results with a price become observations."""

    def test_a_price_in_a_snippet_becomes_an_observation(self):
        prices = search(
            [result("https://todocoleccion.net/lote/1", "Sello 2867", "usado", "12,50 €")]
        ).prices("2867")

        assert len(prices) == 1
        observation = prices[0]
        assert observation.price == Decimal("12.50")
        assert observation.kind == "ask"
        assert observation.condition == "used"
        assert observation.subject_code == "2867"
        assert observation.currency == "EUR"

    def test_a_result_from_another_host_is_ignored(self):
        prices = search(
            [result("https://example.test/x", "Sello 2867", "", "99 €")]
        ).prices("2867")

        assert prices == []

    def test_a_result_without_a_price_is_skipped(self):
        prices = search(
            [result("https://todocoleccion.net/lote/1", "Sello 2867", "consultar")]
        ).prices("2867")

        assert prices == []

    def test_several_results_are_all_kept(self):
        prices = search(
            [
                result("https://todocoleccion.net/lote/1", "", "nuevo, sin charnela", "10,00 €"),
                result("https://ebay.es/itm/2", "", "usado", "12,00 €"),
            ]
        ).prices("2867")

        assert len(prices) == 2
        assert {price.condition for price in prices} == {"mnh", "used"}

    def test_a_bare_nuevo_is_unknown_not_mnh(self):
        """Mint with a hinge is not mint never hinged, and guessing is worse."""
        prices = search(
            [result("https://todocoleccion.net/lote/1", "", "nuevo", "10,00 €")]
        ).prices("2867")

        assert prices[0].condition == "unknown"

    def test_the_results_are_capped(self):
        results = [
            result(f"https://todocoleccion.net/lote/{index}", "", "usado", "10,00 €")
            for index in range(20)
        ]

        assert len(search(results).prices("2867")) == 8


class TestPriceParsing:
    """The narrow formats it understands, and the ones it refuses."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("12,50 €", "12.50"),
            ("12.50 EUR", "12.50"),
            ("EUR 9,99", "9.99"),
            ("€ 9", "9.00"),
            ("desde 8 € gastos aparte", "8.00"),
            ("sin precio", None),
            ("", None),
        ],
    )
    def test_the_price_is_read(self, text, expected):
        price = SearchPrices.price_in(text)

        assert price == (None if expected is None else Decimal(expected))


class TestConfiguration:
    """A backend without URL or key is a deployment problem."""

    def test_no_backend_is_a_configuration_error(self):
        source = SearchPrices(client=HttpClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))), url="", key="")

        with pytest.raises(SourceConfigurationError):
            source.prices("2867")

    def test_a_refused_key_is_a_configuration_error(self):
        from ai_api.sources.errors import SourceError

        with pytest.raises(SourceError):
            search([], status_code=403).prices("2867")

    def test_a_broken_backend_is_unavailable(self):
        with pytest.raises(SourceUnavailable):
            search([], status_code=503).prices("2867")
