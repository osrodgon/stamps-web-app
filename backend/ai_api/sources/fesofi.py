"""Fesofi as a catalogue, not as a HTML page to scrape (plan step A6, first slice).

The Fesofi store exposes its products through the WooCommerce Store API, and the
series name and the year are **attributes** on them. That is what makes a lookup
by "contains these words" possible without a search engine:

    GET /products/attributes/5/terms?search=navidad   -> the series terms
    GET /products?attributes[0][attribute]=pa_titulo-serie&attributes[0][term_id]=5289
                 &attributes[1][attribute]=pa_ano-de-emision&attributes[1][term_id]=22648

returns the two 1986 Christmas stamps, and nothing else. The term search is a
partial match, case-insensitive, which is the behaviour the name lookup needs: a
series comes back when its name *contains* the words, not when it matches them
exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_api.sources.http import HttpClient
from ai_api.sources.store import StoreCatalogue
from ai_api.text import snippet, strip_html


# The name the caller gives us can be the series title or the motive of one of
# its stamps ("la sagrada familia" is the motive of the 1986 Christmas stamp, whose
# series is "Navidad"), so both attributes are searched.
SERIES_ATTRIBUTE, SERIES_TAXONOMY = 5, "pa_titulo-serie"
MOTIVE_ATTRIBUTE, MOTIVE_TAXONOMY = 6, "pa_motivo-sello"
SEARCH_ATTRIBUTES = (
    (SERIES_ATTRIBUTE, SERIES_TAXONOMY, 0),
    (MOTIVE_ATTRIBUTE, MOTIVE_TAXONOMY, 1),
)
YEAR_ATTRIBUTE = 22
YEAR_TAXONOMY = "pa_ano-de-emision"

# A term search can return dozens of terms; after the top ones the year has
# almost always told us which is the right series, and every candidate costs a
# request.
MAX_CANDIDATES = 10

# What a product carries, named the way the rest of the pipeline already speaks
# (`clean_scraped_data` produces the same keys, so the caller can swap one for the
# other).
SERIES_FROM_ATTRIBUTES = {
    "issue_name": "Título Serie",
    "year": "Año de Emisión",
    "issue_date": "Fecha De Emisión",
    "printer": "Imprenta",
    "print_type": "Impresión",
    # No attribute says Sello / Hoja Bloque; "Formato" is the size (40,9 x 28,8 mm),
    # so stamp_type is left for the model to infer from the motive and the text.
    "series_values": "Valores De La Serie",
    "engraver": "Grabador",
    "print_run": "Tirada",
    "perforation": "Dentado",
}

STAMP_FROM_ATTRIBUTES = {
    "edifil_code": "Número EDIFIL",
    "fesofi_code": "Número Fesofi",
    "motive": "Motivo Sello",
    "face_value": "Facial",
    "color": "Color",
    "perforation": "Dentado",
    "total_print_run": "Tirada",
    "format": "Formato",
}


@dataclass(frozen=True)
class Match:
    """What the catalogue answered: the products, and why when there are none.

    `score` is the share of the asked words the series name covers, so 1.0 means
    every word was there. `gap` is written for a human: it is what the endpoint
    says when identity could not be established.
    """

    products: List[dict] = field(default_factory=list)
    term: Optional[dict] = None
    score: float = 0.0
    candidates: List[str] = field(default_factory=list)
    gap: Optional[str] = None

    @property
    def found(self) -> bool:
        """True when there is at least one product to work with."""
        return bool(self.products)

API_ROOT = "https://catalogodesellos.fesofi.es/wp-json/wc/store/v1"

class FesofiCatalogue(StoreCatalogue):
    """Look products up in the Fesofi store by series name and year."""

    name = "fesofi"
    root = "https://catalogodesellos.fesofi.es/wp-json/wc/store/v1"

    def _products(self, term: dict, year_term: Optional[int] = None) -> List[dict]:
        """Return the products of one term, in that year when there is one."""
        filters = [(YEAR_TAXONOMY, year_term)] if year_term is not None else None
        return super()._products(term, filters)

    def _year_term(self, year: str) -> Optional[int]:
        """Return the term id of the year attribute, or None if it does not exist."""
        return self._term_id(YEAR_ATTRIBUTE, year)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def find_product_urls(self, name: str, date: str = "") -> List[str]:
        """Return the product pages of the series the name points at."""
        return [
            product["permalink"]
            for product in self.identify(name, date).products
            if product.get("permalink")
        ]

    def find_products(self, name: str, date: str = "") -> List[dict]:
        """Return the products themselves, with their attributes."""
        return self.identify(name, date).products

    def identify(self, name: str, date: str = "") -> Match:
        """Find the series that contains the words of `name` in `date`'s year.

        The name can be the series title or the motive of one of its stamps; the
        year is used as a filter and never as a word. A term that covers more of
        the words wins, and an exact word-for-word name beats one that merely
        contains them. Two candidates tied on both are reported as a gap instead of
        picked at random — that is the difference between "the catalogue says so"
        and "we guessed".
        """
        year = self._year_of(f"{name} {date}")
        words = self._words(name)
        if not words:
            return Match(gap="The name has no words to search for.")

        query = set(words)
        candidates = self._candidates(words)
        if not candidates:
            return Match(
                gap=f"No series or motive in the catalogue contains "
                    f"{', '.join(sorted(query))}."
            )

        year_term = self._year_term(year) if year else None
        hits = []
        best_coverage = 0
        for term in candidates:
            coverage = self._coverage(query, term.get("name", ""))
            # The candidates come ordered by coverage, so once one hit is found,
            # anything below it cannot tie with it and is not worth a request.
            if hits and coverage < best_coverage:
                break
            products = self._products(term, year_term)
            if not products:
                continue
            hits.append(
                (
                    coverage,
                    self._is_exact(query, term.get("name", "")),
                    term.get("attribute"),
                    term,
                    products,
                )
            )
            best_coverage = max(best_coverage, coverage)

        if not hits:
            where = f" in {year}" if year else ""
            return Match(
                gap=f"Nothing matches {', '.join(sorted(query))}{where}.",
                candidates=[term.get("name", "") for term in candidates[:5]],
            )

        # More words covered first, then an exact name, then the series title over
        # a stamp motive.
        hits.sort(key=lambda hit: (-hit[0], not hit[1], hit[2]))
        best_coverage, best_exact, best_attribute, term, products = hits[0]

        rivals = [
            hit[3].get("name", "")
            for hit in hits[1:]
            if (hit[0], hit[1], hit[2]) == (best_coverage, best_exact, best_attribute)
        ]
        if rivals:
            names = ", ".join([term.get("name", "")] + rivals)
            return Match(
                gap=f"{names} match the same words; the year does not separate them.",
                candidates=[term.get("name", "")] + rivals,
            )

        return Match(
            products=self._whole_series(products, year_term, best_attribute),
            term=term,
            score=round(best_coverage / len(query), 2),
        )

    def _whole_series(
        self, products: List[dict], year_term: Optional[int], attribute: Optional[int]
    ) -> List[dict]:
        """Widen a match on one stamp to the series it belongs to.

        Asking by motive ("la sagrada familia") finds the stamp, but the report is
        about the series, so the rest of it is fetched from the title the product
        itself carries. A match already on a series title costs nothing.
        """
        if not products or attribute == SERIES_ATTRIBUTE:
            return products

        title = self._attributes(products[0]).get(self._normalise("Título Serie"))
        if not title:
            return products

        for term in self._terms(SERIES_ATTRIBUTE, title):
            if self._normalise(term.get("name", "")) != self._normalise(title):
                continue
            series_term = {
                **term,
                "attribute": SERIES_ATTRIBUTE,
                "taxonomy": SERIES_TAXONOMY,
            }
            wider = self._products(series_term, year_term)
            if len(wider) > len(products):
                self.log.debug(
                    f"motive match widened to the series '{title}' "
                    f"({len(products)} -> {len(wider)} products)"
                )
                return wider

        return products

    def facts(self, products: List[dict]) -> Dict[str, Any]:
        """Turn the products into the shape the rest of the pipeline speaks.

        `serie_info` and `stamps` carry the same keys `clean_scraped_data`
        produces, so the model sees the same input whether the data came from the
        API or from a scraped page — but read from the attributes, not guessed from
        a HTML table.
        """
        if not products:
            return {}

        first = self._attributes(products[0])
        serie_info = {
            key: first.get(self._normalise(attribute))
            for key, attribute in SERIES_FROM_ATTRIBUTES.items()
        }

        stamps = []
        for product in products:
            attributes = self._attributes(product)
            stamp = {
                key: attributes.get(self._normalise(attribute))
                for key, attribute in STAMP_FROM_ATTRIBUTES.items()
            }
            stamp["desc_snippet"] = snippet(
                strip_html(product.get("description") or "")
            )
            stamps.append(stamp)

        stamps.sort(key=self._order)
        return {"serie_info": serie_info, "stamps": stamps}

    # ------------------------------------------------------------------
    # Terms
    # ------------------------------------------------------------------

    def _candidates(self, words: List[str]) -> List[dict]:
        """Return the terms that contain the words, best cover first.

        Both the series title and the stamp motive are searched, and every
        candidate is kept, not only the best one: "Castillos de España" with year
        2007 has no products, while the 2007 series is under "Castillos" — the
        second best match — and stopping at the first would return nothing.
        """
        seen: Dict[tuple, dict] = {}
        order: Dict[tuple, int] = {}

        for attribute, taxonomy, rank in SEARCH_ATTRIBUTES:
            for word in words:
                for term in self._terms(attribute, word):
                    key = (attribute, int(term["id"]))
                    if key not in seen:
                        seen[key] = {**term, "attribute": attribute, "taxonomy": taxonomy}
                        order[key] = rank

        if not seen:
            return []

        scored = []
        for key, term in seen.items():
            name = self._normalise(term.get("name", ""))
            coverage = sum(1 for word in words if word in name)
            if coverage == 0:
                continue
            scored.append((coverage, order[key], len(name), key[1], term))

        # More words covered first; then the series title before a motive; then
        # the shortest name (the closest to what was asked) and the id, so the
        # order is stable.
        scored.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        return [term for *_, term in scored[:MAX_CANDIDATES]]
