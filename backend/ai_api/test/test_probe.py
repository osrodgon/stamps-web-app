"""Unit tests for the A0 probe helpers (no network, no database)."""

import json

from ai_api import probe


ROBOTS = """
User-agent: *
Crawl-delay: 10
Disallow: /en_GB/collectables/search
Disallow: /*/account/
Allow: /en_GB/collectables/search/allowed
"""

DELCAMPE_HTML = """
<div id="item-111" data-watch-item>
  <a class="item-link" href="/en_GB/collectables/stamps/spain/x-111.html">
    <h2 class="item-title font-md font-normal">ESPANA 1992 EDIFIL 3164 usado</h2>
  </a>
  <div class="selling-type" title="Auction"></div>
  <strong class="item-price font-xl nowrap">&euro;4.50</strong>
</div>
<div id="item-222">
  <a class="item-link" href="/en_GB/collectables/stamps/spain/y-222.html">
    <h2 class="item-title font-md font-normal">Spain 1992 Expo Sevilla Ed 3164-87</h2>
  </a>
  <strong class="item-price font-xl nowrap">&euro;3.50</strong>
</div>
"""

FESOFI_JSON = json.dumps(
    [
        {
            "name": "3196",
            "sku": "3196",
            "permalink": "https://catalogodesellos.fesofi.es/producto/3196/",
            "prices": {"price": "0", "currency_code": "EUR"},
            "attributes": [
                {
                    "name": "Número EDIFIL",
                    "terms": [{"name": "3188"}],
                },
                {
                    "name": "Título Serie",
                    "terms": [{"name": "Expo 92 Sevilla"}],
                },
            ],
        }
    ]
)

IBERPHIL_SOLD = """
<html><body>
<div class="alert alert-secondary text-center">
  <span>Adjudicación</span> 90€
</div>
<span class="text-muted">Puja inicial</span> <b class="text-muted price">90€</b>
<meta name="description" content="SOBRE 1847. EDIFIL 5. MAGNIFICA">
</body></html>
"""

IBERPHIL_UNSOLD = """
<html><body>
<div class="alert alert-secondary text-center">
  <span>Adjudicación</span> 0€
</div>
<span class="text-muted">Puja inicial</span> <b class="text-muted price">Libre</b>
</body></html>
"""

IBERPHIL_SOLD_TABLE = """
<table>
  <tr><th>N&deg; Lote</th><th>Clasificación</th><th>Puja inicial (&euro;)</th></tr>
  <tr><td>1027</td><td>Bibliografía</td><td>5,00</td></tr>
  <tr><td>1036</td><td>Bibliografía</td><td>90,00</td></tr>
</table>
<a href="/es/subastas-sellos/46-x-20-05-2026/lote-1027-%257C">1027</a>
"""


class TestRobotsRule:
    """The robots.txt reading the probe reports."""

    def test_disallowed_path_returns_the_rule(self):
        assert probe.robots_rule(ROBOTS, "/en_GB/collectables/search") == (
            "Disallow: /en_GB/collectables/search"
        )

    def test_allowed_path_returns_none(self):
        assert probe.robots_rule(ROBOTS, "/en/stamps/list/") is None

    def test_allow_wins_over_disallow_on_the_same_length(self):
        assert probe.robots_rule(ROBOTS, "/en_GB/collectables/search/allowed") is None

    def test_wildcard_pattern_matches(self):
        assert probe.robots_rule(ROBOTS, "/en_GB/account/login") == "Disallow: /*/account/"

    def test_named_agent_group_beats_the_wildcard(self):
        text = "User-agent: *\nDisallow: /\n\nUser-agent: stamps-web-app-probe\nAllow: /\n"
        assert probe.robots_rule(text, "/datadesk/") is None


class TestDetection:
    """Response-shape and challenge detection."""

    def test_detect_anubis_challenge(self):
        html = "<title>Colnect Collectors Protection</title>"
        assert probe.detect_challenge(html) == "anubis"

    def test_no_challenge_in_a_plain_page(self):
        assert probe.detect_challenge("<html><body>hola</body></html>") is None

    def test_response_shape_names_json(self):
        assert probe.response_shape("application/json; charset=UTF-8", b"[]") == "json"

    def test_response_shape_names_html(self):
        assert probe.response_shape("text/html", b"<html>") == "html"

    def test_response_shape_names_an_empty_body(self):
        assert probe.response_shape("application/json", b"") == "empty"

    def test_verdict_reads_a_bot_challenge(self):
        assert probe.verdict(200, "anubis") == "blocked by a bot challenge (anubis)"

    def test_verdict_reads_the_http2_requirement(self):
        assert probe.verdict(426, None) == "rejected: HTTP/2 required by the server"

    def test_verdict_reads_a_missing_key(self):
        assert probe.verdict(401, None) == "reachable, credentials required (401)"


class TestDelcampeParsing:
    """The Delcampe card parser and the URL it asks for."""

    def test_search_url_uses_the_term_parameter(self):
        url = probe.delcampe_search_url(probe.SUBJECTS[3])
        assert "term=3164+1992" in url
        assert "?q=" not in url

    def test_cards_carry_title_price_and_selling_type(self):
        cards = probe.parse_delcampe_cards(DELCAMPE_HTML)

        assert len(cards) == 2
        assert cards[0]["price"] == "€4.50"
        assert cards[0]["selling_type"] == "Auction"
        assert cards[1]["title"] == "Spain 1992 Expo Sevilla Ed 3164-87"

    def test_limit_is_respected(self):
        assert len(probe.parse_delcampe_cards(DELCAMPE_HTML, limit=1)) == 1

    def test_an_empty_page_yields_no_cards(self):
        assert probe.parse_delcampe_cards("<html></html>") == []


class TestFesofiParsing:
    """The WooCommerce Store API product reader."""

    def test_product_attributes_become_a_map(self):
        products = probe.parse_fesofi_products(FESOFI_JSON)

        assert products[0]["name"] == "3196"
        assert products[0]["attributes"]["Número EDIFIL"] == "3188"
        assert products[0]["attributes"]["Título Serie"] == "Expo 92 Sevilla"

    def test_the_lookup_url_asks_by_sku(self):
        assert "?sku=3196" in probe.fesofi_search_url(probe.SUBJECTS[3])

    def test_a_non_json_body_yields_no_products(self):
        assert probe.parse_fesofi_products("<html></html>") == []


class TestIberphilParsing:
    """The lot page and the sold-lots table."""

    def test_a_sold_lot_carries_its_hammer_price(self):
        lot = probe.parse_iberphil_lot(IBERPHIL_SOLD)

        assert lot["hammer_price"] == "90"
        assert lot["starting_price"] == "90"
        assert lot["sold"] is True
        assert lot["mentions_edifil"] is True

    def test_an_unsold_lot_has_a_zero_hammer_and_a_free_start(self):
        lot = probe.parse_iberphil_lot(IBERPHIL_UNSOLD)

        assert lot["hammer_price"] == "0"
        assert lot["sold"] is False
        assert lot["starting_free"] is True

    def test_the_sold_lots_table_lists_the_starting_price_only(self):
        rows = probe.parse_iberphil_sold_lots(IBERPHIL_SOLD_TABLE)

        assert rows[0]["N° Lote"] == "1027"
        assert rows[0]["Puja inicial (€)"] == "5,00"

    def test_lot_links_are_collected_once(self):
        links = probe.parse_iberphil_lot_links(IBERPHIL_SOLD_TABLE + IBERPHIL_SOLD_TABLE)

        assert len(links) == 1
        assert links[0].endswith("/lote-1027-%257C")


class TestSubjects:
    """The five series the probe walks."""

    def test_every_subject_carries_both_catalogue_codes(self):
        assert len(probe.SUBJECTS) == 5
        for subject in probe.SUBJECTS:
            assert subject.first_edifil
            assert subject.first_fesofi
            assert subject.stamps > 0

    def test_query_is_the_code_and_the_year(self):
        assert probe.SUBJECTS[3].query == "3164 1992"

    def test_the_report_payload_has_no_property(self):
        payload = probe.SUBJECTS[0].as_dict()

        assert "query" not in payload
        assert payload["first_fesofi"] == "0001"
