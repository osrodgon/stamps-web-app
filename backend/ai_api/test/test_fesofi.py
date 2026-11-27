"""Tests for the Fesofi catalogue lookup (plan step A6, first slice).

The behaviour that matters: a series comes back when its name **contains** the
words, not when it matches them exactly. Everything runs over a fake transport.
"""

import httpx
import pytest

from ai_api.sources.errors import SourceUnavailable
from ai_api.sources.fesofi import FesofiCatalogue
from ai_api.sources.http import HttpClient


API = "https://catalogodesellos.fesofi.es/wp-json/wc/store/v1"

SERIES_TERMS = {
    "navidad": [
        {"id": 5289, "name": "Navidad"},
        {"id": 15734, "name": "Navidad 2004."},
        {"id": 29204, "name": "NAVIDAD 2024. Tradición arrastre de latas"},
    ],
    "castillos": [
        {"id": 4111, "name": "Castillos"},
        {"id": 4112, "name": "Castillos de España"},
        {"id": 4113, "name": "Castillos españoles"},
    ],
    "espana": [
        {"id": 4112, "name": "Castillos de España"},
    ],
    "expo": [
        {"id": 5000, "name": "España exporta"},
        {"id": 5001, "name": "Expo 92"},
        {"id": 5002, "name": "Expo. Filatélica de América y Europa"},
    ],
    "92": [
        {"id": 5001, "name": "Expo 92"},
    ],
}


MOTIVE_TERMS = {
    "sagrada": [
        {"id": 12207, "name": "La Sagrada Familia"},
        {"id": 10641, "name": "La Sagrada Familia. Valladolid"},
        {"id": 4181, "name": "«La Sagrada Familia» de El Greco"},
    ],
    "familia": [
        {"id": 12207, "name": "La Sagrada Familia"},
        {"id": 10641, "name": "La Sagrada Familia. Valladolid"},
    ],
    "navidad": [
        {"id": 14930, "name": "«Navidad» (Goyo Domínguez)"},
    ],
}


def transport(handler) -> HttpClient:
    """A client wired to a fake Fesofi."""
    return HttpClient(
        allowed_hosts=["catalogodesellos.fesofi.es"],
        transport=httpx.MockTransport(handler),
        cache_ttl=0,
    )


def fesofi(handler) -> FesofiCatalogue:
    """A catalogue over the fake transport."""
    return FesofiCatalogue(client=transport(handler))


def router(year_terms=None, products=None, terms=None):
    """Build a handler that answers the three endpoints from fixed data."""
    year_terms = year_terms or []
    products = products or []
    terms = terms or SERIES_TERMS

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/attributes/5/terms"):
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=terms.get(word, []))
        if path.endswith("/attributes/6/terms"):
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=MOTIVE_TERMS.get(word, []))
        if path.endswith("/attributes/22/terms"):
            return httpx.Response(200, json=year_terms)
        if path.endswith("/products"):
            return httpx.Response(200, json=products)
        return httpx.Response(404)

    return handler


class TestText:
    """The comparison is by words, case and accents aside."""

    def test_accents_and_case_do_not_matter(self):
        assert FesofiCatalogue._normalise("España") == "espana"
        assert FesofiCatalogue._normalise("NAVIDAD") == "navidad"

    def test_stopwords_are_dropped(self):
        assert FesofiCatalogue._words("Castillos de España") == ["castillos", "espana"]

    def test_the_year_is_not_a_word(self):
        assert FesofiCatalogue._words("Navidad 1986") == ["navidad"]

    def test_a_short_number_is_kept(self):
        assert FesofiCatalogue._words("Expo 92") == ["expo", "92"]

    def test_the_year_comes_from_a_full_date(self):
        assert FesofiCatalogue._year_of("2007-09-10") == "2007"

    def test_a_name_without_a_year_has_none(self):
        assert FesofiCatalogue._year_of("Navidad") is None


class TestMotive:
    """The name can be the motive of a stamp, not only the series title."""

    def test_a_motive_finds_the_stamp(self):
        asked = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[{"id": 22648, "name": "1986"}])
            if request.url.path.endswith("/products"):
                params = dict(request.url.params)
                asked["taxonomy"] = params["attributes[0][attribute]"]
                if params["attributes[0][term_id]"] == "10641":
                    return httpx.Response(
                        200,
                        json=[{"permalink": "https://catalogodesellos.fesofi.es/producto/2883/"}],
                    )
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/attributes/6/terms"):
                word = request.url.params.get("search", "")
                return httpx.Response(200, json=MOTIVE_TERMS.get(word, []))
            return httpx.Response(200, json=[])

        urls = fesofi(handler).find_product_urls("la sagrada familia 1986")

        assert urls == ["https://catalogodesellos.fesofi.es/producto/2883/"]
        assert asked["taxonomy"] == "pa_motivo-sello"

    def test_the_series_title_wins_over_a_motive_with_the_same_cover(self):
        asked = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                asked.append(dict(request.url.params)["attributes[0][attribute]"])
                return httpx.Response(200, json=[{"permalink": "https://x/1/"}])
            if request.url.path.endswith("/attributes/6/terms"):
                word = request.url.params.get("search", "")
                return httpx.Response(200, json=MOTIVE_TERMS.get(word, []))
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[])
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=SERIES_TERMS.get(word, []))

        fesofi(handler).find_product_urls("navidad")

        assert asked[0] == "pa_titulo-serie"


class TestIdentify:
    """The match is scored, and a tie is a gap instead of a coin toss."""

    def test_an_exact_name_wins_without_a_year(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                return httpx.Response(200, json=[{"name": "hit", "permalink": "https://x/1/"}])
            if request.url.path.endswith("/attributes/6/terms"):
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[])
            return httpx.Response(200, json=SERIES_TERMS["navidad"])

        match = fesofi(handler).identify("navidad")

        assert match.found
        assert match.term["name"] == "Navidad"
        assert match.score == 1.0

    def test_a_tie_between_two_series_is_a_gap(self):
        terms = [
            {"id": 1, "name": "Castillos"},
            {"id": 2, "name": "Castillos"},
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                return httpx.Response(200, json=[{"name": "hit", "permalink": "https://x/1/"}])
            if request.url.path.endswith("/attributes/6/terms"):
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[])
            return httpx.Response(200, json=terms)

        match = fesofi(handler).identify("castillos")

        assert not match.found
        assert "Castillos, Castillos" in match.gap
        assert match.candidates == ["Castillos", "Castillos"]

    def test_nothing_matching_is_a_gap_with_the_words(self):
        match = fesofi(router()).identify("zzzz")

        assert not match.found
        assert "zzzz" in match.gap

    def test_a_year_without_products_is_a_gap(self):
        handler = router(year_terms=[{"id": 22648, "name": "1986"}], products=[])

        match = fesofi(handler).identify("navidad 1986")

        assert not match.found
        assert "1986" in match.gap

    def test_the_score_is_the_share_of_words_covered(self):
        handler = router(
            products=[{"name": "hit", "permalink": "https://x/1/"}],
            terms={"castillos": [{"id": 4111, "name": "Castillos"}], "92": []},
        )

        match = fesofi(handler).identify("castillos 92")

        assert match.score == 0.5


class TestFacts:
    """The attributes become the shape the pipeline already speaks."""

    PRODUCT = {
        "name": "2884",
        "permalink": "https://catalogodesellos.fesofi.es/producto/2884/",
        "description": "<p>Felipe de Bigarny, <b>más conocido</b> por Felipe de Borgoña.</p>",
        "attributes": [
            {"name": "Título Serie", "terms": [{"name": "Navidad"}]},
            {"name": "Año de Emisión", "terms": [{"name": "1986"}]},
            {"name": "Fecha de Emisión", "terms": [{"name": "16 noviembre 1986"}]},
            {"name": "Formato", "terms": [{"name": "Hoja"}]},
            {"name": "Número EDIFIL", "terms": [{"name": "2868"}]},
            {"name": "Número Fesofi", "terms": [{"name": "2884"}]},
            {"name": "Motivo Sello", "terms": [{"name": "Natividad. Toledo"}]},
            {"name": "Facial", "terms": [{"name": "48 pta"}]},
            {"name": "Color", "terms": [{"name": "multicolor"}]},
            {"name": "Dentado", "terms": [{"name": "13 3/4"}]},
            {"name": "Tirada", "terms": [{"name": "4.000.000"}]},
        ],
    }

    def test_series_keys_match_the_scraper(self):
        facts = fesofi(router()).facts([self.PRODUCT])
        serie = facts["serie_info"]

        assert serie["issue_name"] == "Navidad"
        assert serie["year"] == "1986"
        # The catalogue writes "Fecha De Emisión" with a capital D.
        assert serie["issue_date"] == "16 noviembre 1986"
        # "Formato" is the size, not the type: stamp_type is not invented here.
        assert "stamp_type" not in serie

    def test_stamp_keys_and_codes(self):
        stamp = fesofi(router()).facts([self.PRODUCT])["stamps"][0]

        assert stamp["edifil_code"] == "2868"
        assert stamp["fesofi_code"] == "2884"
        assert stamp["motive"] == "Natividad. Toledo"
        assert stamp["face_value"] == "48 pta"
        assert stamp["total_print_run"] == "4.000.000"

    def test_the_description_is_text_not_html(self):
        stamp = fesofi(router()).facts([self.PRODUCT])["stamps"][0]

        assert "<p>" not in stamp["desc_snippet"]
        assert "más conocido" in stamp["desc_snippet"]

    def test_stamps_are_ordered_by_their_code(self):
        other = {
            "name": "2883",
            "attributes": [
                {"name": "Número EDIFIL", "terms": [{"name": "2867"}]},
                {"name": "Número Fesofi", "terms": [{"name": "2883"}]},
            ],
        }

        stamps = fesofi(router()).facts([self.PRODUCT, other])["stamps"]

        assert [stamp["edifil_code"] for stamp in stamps] == ["2867", "2868"]

    def test_a_sheet_keeps_its_own_fesofi_code(self):
        """The FDC sheet has no Edifil; it is ordered by its Fesofi code, not dropped."""
        sheet = {
            "name": "2884SPD",
            "attributes": [{"name": "Número Fesofi", "terms": [{"name": "2884SPD"}]}],
        }

        stamps = fesofi(router()).facts([self.PRODUCT, sheet])["stamps"]

        assert [stamp["fesofi_code"] for stamp in stamps] == ["2884", "2884SPD"]
        assert stamps[-1]["edifil_code"] is None

    def test_no_products_is_an_empty_dict(self):
        assert fesofi(router()).facts([]) == {}


class TestLookup:
    """Words in, product pages out."""

    def test_the_series_whose_name_contains_the_words_is_found(self):
        handler = router(
            year_terms=[{"id": 22648, "name": "1986"}],
            products=[
                {"permalink": "https://catalogodesellos.fesofi.es/producto/2884/"},
                {"permalink": "https://catalogodesellos.fesofi.es/producto/2883/"},
            ],
        )

        urls = fesofi(handler).find_product_urls("navidad 1986")

        assert urls == [
            "https://catalogodesellos.fesofi.es/producto/2884/",
            "https://catalogodesellos.fesofi.es/producto/2883/",
        ]

    def test_the_year_filters_the_products(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[{"id": 22648, "name": "1986"}])
            if request.url.path.endswith("/products"):
                seen["params"] = dict(request.url.params)
                return httpx.Response(200, json=[])
            return httpx.Response(200, json=SERIES_TERMS["navidad"])

        fesofi(handler).find_product_urls("navidad", "1986")

        assert seen["params"]["attributes[1][attribute]"] == "pa_ano-de-emision"
        assert seen["params"]["attributes[1][term_id]"] == "22648"

    def test_all_the_words_beat_one_of_them(self):
        asked = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                asked.append(dict(request.url.params)["attributes[0][term_id]"])
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[])
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=SERIES_TERMS.get(word, []))

        fesofi(handler).find_product_urls("Castillos de España")

        # 4112 is "Castillos de España", the only term with both words: first.
        assert asked[0] == "4112"

    def test_a_candidate_without_products_lets_the_next_one_answer(self):
        """The 2007 "Castillos" series lives under a term without the "de España"."""
        asked = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[{"id": 22621, "name": "2007"}])
            if request.url.path.endswith("/attributes/6/terms"):
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/products"):
                params = dict(request.url.params)
                term = params["attributes[0][term_id]"]
                asked.append(term)
                if term == "4111":
                    return httpx.Response(
                        200,
                        json=[{"permalink": "https://catalogodesellos.fesofi.es/producto/4605/"}],
                    )
                return httpx.Response(200, json=[])
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=SERIES_TERMS.get(word, []))

        urls = fesofi(handler).find_product_urls("castillos de españa 2007")

        # The best-covered term is asked first; when it has nothing in that year,
        # the next one answers.
        assert asked[0] == "4112"
        assert "4111" in asked
        assert urls == ["https://catalogodesellos.fesofi.es/producto/4605/"]

    def test_a_short_number_helps_pick_the_right_series(self):
        asked = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/products"):
                asked.append(dict(request.url.params)["attributes[0][term_id]"])
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/attributes/22/terms"):
                return httpx.Response(200, json=[])
            word = request.url.params.get("search", "")
            return httpx.Response(200, json=SERIES_TERMS.get(word, []))

        fesofi(handler).find_product_urls("expo 92")

        # "Expo 92" (both words) is asked before "España exporta" (one).
        assert asked[0] == "5001"

    def test_nothing_matching_is_empty(self):
        handler = router()

        assert fesofi(handler).find_product_urls("zzzz") == []

    def test_a_series_without_products_in_that_year_yields_nothing(self):
        handler = router(
            year_terms=[{"id": 22648, "name": "1986"}],
            products=[],
        )

        assert fesofi(handler).find_product_urls("navidad 1986") == []

    def test_a_broken_catalogue_raises(self):
        handler = lambda request: httpx.Response(500, text="boom")

        with pytest.raises(SourceUnavailable):
            fesofi(handler).find_product_urls("navidad")

    def test_products_carry_their_attributes(self):
        handler = router(
            year_terms=[{"id": 22648, "name": "1986"}],
            products=[
                {
                    "name": "2884",
                    "permalink": "https://catalogodesellos.fesofi.es/producto/2884/",
                    "attributes": [
                        {"name": "Número EDIFIL", "terms": [{"name": "2868"}]},
                        {"name": "Título Serie", "terms": [{"name": "Navidad"}]},
                    ],
                }
            ],
        )

        products = fesofi(handler).find_products("navidad 1986")

        assert products[0]["name"] == "2884"
        assert products[0]["attributes"][0]["terms"][0]["name"] == "2868"
