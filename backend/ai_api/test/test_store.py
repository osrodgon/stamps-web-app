"""Tests for the shared Store API reader (plan step A7).

Both catalogues speak the same API, so the parts that are not about stamps are
tested once, here.
"""

import httpx
import pytest

from ai_api.sources.errors import SourceError, SourceUnavailable
from ai_api.sources.http import HttpClient
from ai_api.sources.store import StoreCatalogue


class Shop(StoreCatalogue):
    """A store with the two attributes these tests use."""

    name = "shop"
    root = "https://shop.test/wp-json/wc/store/v1"


def shop(handler) -> Shop:
    """A catalogue over a fake transport."""
    client = HttpClient(
        allowed_hosts=["shop.test"],
        transport=httpx.MockTransport(handler),
        cache_ttl=0,
    )
    return Shop(client=client)


class TestTerms:
    """A code is resolved to its term, exactly."""

    def test_an_exact_term_is_returned(self):
        handler = lambda request: httpx.Response(
            200, json=[{"id": 1, "name": "28"}, {"id": 2, "name": "2867"}]
        )

        assert shop(handler)._term_id(45, "2867") == 2

    def test_a_missing_term_is_none(self):
        handler = lambda request: httpx.Response(200, json=[{"id": 1, "name": "28"}])

        assert shop(handler)._term_id(45, "2867") is None

    def test_the_search_word_is_sent(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["search"] = request.url.params.get("search")
            return httpx.Response(200, json=[])

        shop(handler)._term_id(45, "2867")

        assert seen["search"] == "2867"


class TestProducts:
    """The filters go into the query string."""

    def test_the_term_and_the_extra_filters_are_sent(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(dict(request.url.params))
            return httpx.Response(200, json=[])

        shop(handler)._products(
            {"id": 429, "taxonomy": "pa_sello-numeracion"}, [("pa_sello-ano", 7)]
        )

        assert seen["attributes[0][attribute]"] == "pa_sello-numeracion"
        assert seen["attributes[0][term_id]"] == "429"
        assert seen["attributes[1][attribute]"] == "pa_sello-ano"
        assert seen["attributes[1][term_id]"] == "7"

    def test_a_server_error_is_unavailable(self):
        handler = lambda request: httpx.Response(503)

        with pytest.raises(SourceUnavailable):
            shop(handler)._products({"id": 1, "taxonomy": "pa_x"})

    def test_a_non_json_answer_is_a_source_error(self):
        handler = lambda request: httpx.Response(200, text="<html>")

        with pytest.raises(SourceError):
            shop(handler)._products({"id": 1, "taxonomy": "pa_x"})


class TestPrice:
    """The API sends minor units, and getting that wrong is a factor of 100."""

    def test_minor_units_are_converted(self):
        product = {
            "prices": {
                "price": "1000",
                "currency_code": "EUR",
                "currency_minor_unit": 2,
            }
        }

        assert Shop._price(product) == 10.0

    def test_zero_minor_units_are_major_units(self):
        product = {"prices": {"price": "7", "currency_minor_unit": 0}}

        assert Shop._price(product) == 7.0

    def test_a_product_without_a_price_is_none(self):
        assert Shop._price({"prices": {"price": ""}}) is None
        assert Shop._price({}) is None

    def test_the_currency_is_read(self):
        assert Shop._currency({"prices": {"currency_code": "GBP"}}) == "GBP"
        assert Shop._currency({}) == "EUR"


class TestText:
    """The comparison helpers, shared with the identity lookup."""

    def test_accents_and_case_do_not_matter(self):
        assert Shop._normalise("España") == "espana"

    def test_a_year_is_a_filter_but_part_of_a_name(self):
        assert Shop._words("Navidad 1986") == ["navidad"]
        assert Shop._words("Navidad 1986", keep_years=True) == ["navidad", "1986"]

    def test_the_attributes_are_keyed_without_case_or_accents(self):
        product = {
            "attributes": [
                {"name": "Fecha De Emisión", "terms": [{"name": "16 noviembre 1986"}]}
            ]
        }

        assert Shop._attributes(product)["fecha de emision"] == "16 noviembre 1986"
