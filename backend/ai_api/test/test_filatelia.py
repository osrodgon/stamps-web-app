"""Tests for the price source (plan step A7).

`filatelia.online` answers with asking prices and a condition; getting either wrong
is worse than not asking, so both are pinned here.
"""

from decimal import Decimal

import httpx
import pytest

from ai_api.sources.filatelia import FilateliaCatalogue
from ai_api.sources.http import HttpClient


ROOT = "https://filatelia.online/wp-json/wc/store/v1"


def product(name="Prueba Oficial 100", price="1000", estado="Nuevo (sin circular), Sin charnela", year="2009"):
    """One shop product, the way the Store API returns it."""
    return {
        "id": 6210,
        "name": name,
        "permalink": "https://filatelia.online/tienda/sello/prueba-oficial-100/",
        "prices": {
            "price": price,
            "currency_code": "EUR",
            "currency_minor_unit": 2,
        },
        "attributes": [
            {"name": "Nº Edifil", "terms": [{"name": "100"}]},
            {"name": "Estado", "terms": [{"name": estado}]},
            {"name": "Año", "terms": [{"name": year}]},
        ],
    }


def shop(handler) -> FilateliaCatalogue:
    """The shop over a fake transport."""
    client = HttpClient(
        allowed_hosts=["filatelia.online"],
        transport=httpx.MockTransport(handler),
        cache_ttl=0,
    )
    return FilateliaCatalogue(client=client)


def router(term_id=429, products=None, year_term=7):
    """Answer the three calls the source makes."""
    products = products if products is not None else [product()]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/attributes/45/terms"):
            return httpx.Response(
                200, json=[{"id": term_id, "name": "100"}] if term_id else []
            )
        if request.url.path.endswith("/attributes/2/terms"):
            return httpx.Response(
                200,
                json=[{"id": year_term, "name": "2009"}] if year_term is not None else [],
            )
        if request.url.path.endswith("/products"):
            return httpx.Response(200, json=products)
        return httpx.Response(404)

    return handler


class TestPrices:
    """A code in, one observation per product out."""

    def test_a_price_becomes_an_observation(self):
        observations = shop(router()).prices("100")

        assert len(observations) == 1
        observation = observations[0]
        assert observation.price == Decimal("10.00")  # minor units: 1000 = 10.00 €
        assert observation.currency == "EUR"
        assert observation.kind == "ask"
        assert observation.subject_code == "100"
        assert observation.url.startswith("https://filatelia.online/")

    def test_an_unstocked_code_is_no_answer(self):
        assert shop(router(term_id=None)).prices("2867") == []

    def test_an_empty_code_asks_nothing(self):
        calls = []
        handler = lambda request: calls.append(request.url) or httpx.Response(200, json=[])

        assert shop(handler).prices("") == []
        assert calls == []

    def test_a_product_without_a_price_is_not_zero(self):
        observations = shop(router(products=[product(price="")])).prices("100")

        assert observations == []

    def test_the_year_is_used_as_a_filter(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                seen.update(dict(request.url.params))
            return router()(request)

        shop(handler).prices("100", "2009")

        assert seen["attributes[1][attribute]"] == "pa_sello-ano"
        assert seen["attributes[1][term_id]"] == "7"


class TestCondition:
    """The shop's wording decides which condition the price belongs to."""

    @pytest.mark.parametrize(
        "estado,condition",
        [
            ("Nuevo (sin circular), Sin charnela", "mnh"),
            ("Nuevo, sin fijasellos", "mnh"),
            ("Nuevo con charnela", "mh"),
            ("Nuevo con fijasellos", "mh"),
            ("Usado", "used"),
            ("Usado, matasellado", "used"),
            ("Sin datos", "unknown"),
            ("", "unknown"),
        ],
    )
    def test_the_wording_is_mapped(self, estado, condition):
        assert FilateliaCatalogue.condition_of(estado) == condition

    def test_the_observation_carries_the_condition(self):
        observations = shop(router(products=[product(estado="Usado")])).prices("100")

        assert observations[0].condition == "used"

    def test_an_unknown_condition_is_kept_as_unknown(self):
        observations = shop(router(products=[product(estado="")])).prices("100")

        assert observations[0].condition == "unknown"
