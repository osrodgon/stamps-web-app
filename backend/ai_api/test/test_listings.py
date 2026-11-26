"""Tests for the listing page parsers (plan step A7b).

The pages are saved as they looked when the parser was written: the price in
`lote-precio`, the condition in the title, and a "Vendido el …" line on a sale.
"""

from decimal import Decimal

import pytest

from ai_api.sources.listings import (
    Listing,
    TodoColeccionParser,
    parse,
    parser_for,
)


LIVE = """
<html><body>
  <h1 id="lote-page-h1">ESPAÑA 2007. EDIFIL 4349-4350. CASTILLOS. NUEVO MNH** sin fijasello</h1>
  <div id="lote-info">
    <span class="lote-precio" style="font-size:24px;">6,00 &euro;</span>
    <div>Admite ofertas</div>
    <p><span>Estado del lote: </span> Muy Bueno (nuevo o como nuevo, sin señales de uso)</p>
  </div>
</body></html>
"""

SOLD = """
<html><body>
  <h1 id="lote-page-h1">Edifil 4350 Castillo de Villena Alicante</h1>
  <p>Vendido el 03/09/2026</p>
  <p><span>Estado del lote: </span> Normal (con señales de uso normal)</p>
</body></html>
"""


class TestTodoColeccion:
    """The price and the condition of a listing."""

    def test_a_live_listing_has_price_and_condition(self):
        listing = TodoColeccionParser().parse(LIVE)

        assert listing.price == Decimal("6.00")
        assert listing.condition == "mnh"
        assert listing.sold is False
        assert "CASTILLOS" in listing.title

    def test_a_thousand_separator_is_not_a_decimal(self):
        html = LIVE.replace("6,00", "1.250,00")

        assert TodoColeccionParser().parse(html).price == Decimal("1250.00")

    def test_a_used_title_is_used(self):
        html = LIVE.replace("NUEVO MNH** sin fijasello", "usado, buen estado")

        assert TodoColeccionParser().parse(html).condition == "used"

    def test_a_bare_nuevo_is_unknown(self):
        html = LIVE.replace("NUEVO MNH** sin fijasello", "Nuevo")

        assert TodoColeccionParser().parse(html).condition == "unknown"

    def test_a_sold_page_is_a_sale(self):
        listing = TodoColeccionParser().parse(SOLD)

        assert listing.sold is True
        assert listing.price is None
        assert listing.condition == "unknown"

    def test_a_page_without_a_price_has_none(self):
        html = LIVE.replace("6,00", "")

        assert TodoColeccionParser().parse(html).price is None

    def test_an_empty_page_is_empty(self):
        listing = TodoColeccionParser().parse("")

        assert listing == Listing()


class TestRouting:
    """Which parser reads which host."""

    def test_todocoleccion_is_known(self):
        parser = parser_for("https://www.todocoleccion.net/sellos/x~x1")

        assert isinstance(parser, TodoColeccionParser)

    def test_ebay_is_not_parsed(self):
        assert parser_for("https://www.ebay.es/itm/123") is None

    def test_an_unknown_host_is_not_parsed(self):
        assert parse("https://example.test/x", LIVE) is None

    def test_a_known_host_is_parsed(self):
        listing = parse("https://www.todocoleccion.net/sellos/x~x1", LIVE)

        assert listing is not None
        assert listing.price == Decimal("6.00")
