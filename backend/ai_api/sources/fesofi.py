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

import unicodedata
from typing import Dict, List, Optional

from ai_api.sources.errors import SourceError, SourceUnavailable
from ai_api.sources.http import HttpClient, get_client
from common.log.logger import Logger


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

API_ROOT = "https://catalogodesellos.fesofi.es/wp-json/wc/store/v1"

# Words that carry no identity: without this, "Castillos de España" would never
# match "Castillos de España" because of the "de".
STOPWORDS = frozenset(
    {
        "de", "del", "la", "el", "los", "las", "y", "e", "en", "a", "al",
        "con", "por", "para", "un", "una", "unos", "unas", "serie", "sello",
        "sellos", "hoja", "bloque", "emision", "emisión",
    }
)


class FesofiCatalogue(Logger):
    """Look products up in the Fesofi store by series name and year."""

    def __init__(self, client: Optional[HttpClient] = None) -> None:
        """Take the shared HTTP client, or the one a test injects."""
        super().__init__()
        self.client = client or get_client()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def find_product_urls(self, name: str, date: str = "") -> List[str]:
        """Return the product pages whose series contains the words of `name`.

        Args:
            name: free text, e.g. "Navidad", "navidad 1986", "Castillos de España".
            date: the year or date the caller has; its year is used as a filter.

        Returns:
            Product permalinks, best candidate first. Empty when the catalogue
            has nothing that contains the words.
        """
        year = self._year_of(f"{name} {date}")
        words = self._words(name)
        if not words:
            return []

        terms = self._candidates(words)
        if not terms:
            return []

        year_term = self._year_term(year) if year else None
        for term in terms:
            products = self._products(term, year_term)
            urls = [product.get("permalink") for product in products if product.get("permalink")]
            if urls:
                self.log.debug(
                    f"fesofi: {len(urls)} pages for '{name}' "
                    f"in '{term['name']}'" + (f" ({year})" if year else "")
                )
                return urls

        return []

    def find_products(self, name: str, date: str = "") -> List[dict]:
        """Return the products themselves, with their attributes (used by A6)."""
        year = self._year_of(f"{name} {date}")
        words = self._words(name)
        if not words:
            return []

        year_term = self._year_term(year) if year else None
        for term in self._candidates(words):
            products = self._products(term, year_term)
            if products:
                return products

        return []

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

    def _terms(self, attribute: int, word: str) -> List[dict]:
        """Return the terms of one attribute whose name contains `word`."""
        url = f"{API_ROOT}/products/attributes/{attribute}/terms"
        response = self.client.get(url, params={"search": word, "per_page": 100})

        if response.status_code >= 400:
            raise SourceUnavailable(
                f"Fesofi terms answered HTTP {response.status_code}."
            )

        try:
            terms = response.json()
        except ValueError as error:
            raise SourceError("Fesofi terms did not answer JSON.") from error

        return terms if isinstance(terms, list) else []

    def _year_term(self, year: str) -> Optional[int]:
        """Return the term id of the year attribute, or None if it does not exist."""
        url = f"{API_ROOT}/products/attributes/{YEAR_ATTRIBUTE}/terms"
        response = self.client.get(url, params={"search": year, "per_page": 10})

        if response.status_code >= 400:
            raise SourceUnavailable(
                f"Fesofi years answered HTTP {response.status_code}."
            )

        try:
            terms = response.json()
        except ValueError as error:
            raise SourceError("Fesofi years did not answer JSON.") from error

        for term in terms or []:
            if self._normalise(term.get("name", "")) == year:
                return int(term["id"])

        return None

    def _products(self, term: dict, year_term: Optional[int]) -> List[dict]:
        """Return the products of one term, filtered by year when there is one."""
        params: Dict[str, str] = {
            "attributes[0][attribute]": term["taxonomy"],
            "attributes[0][term_id]": str(term["id"]),
            "per_page": "100",
        }
        if year_term is not None:
            params["attributes[1][attribute]"] = YEAR_TAXONOMY
            params["attributes[1][term_id]"] = str(year_term)

        url = f"{API_ROOT}/products"
        response = self.client.get(url, params=params)

        if response.status_code >= 400:
            raise SourceUnavailable(
                f"Fesofi products answered HTTP {response.status_code}."
            )

        try:
            products = response.json()
        except ValueError as error:
            raise SourceError("Fesofi products did not answer JSON.") from error

        return products if isinstance(products, list) else []

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    @classmethod
    def _words(cls, name: str) -> List[str]:
        """Split a name into comparable words, dropping stopwords and the year."""
        words = []
        for token in cls._normalise(name).split():
            token = token.strip(".,;:()[]«»\"'¡!¿?")
            if not token or token in STOPWORDS or cls._is_year(token):
                continue
            words.append(token)
        return words

    @staticmethod
    def _is_year(token: str) -> bool:
        """Return True for a four-digit year a stamp could have been issued in."""
        return token.isdigit() and len(token) == 4 and 1800 <= int(token) <= 2100

    @classmethod
    def _year_of(cls, text: str) -> Optional[str]:
        """Return the first plausible year found in the text, or None."""
        for token in cls._normalise(text).replace("-", " ").replace("/", " ").split():
            token = token.strip(".,;:()[]")
            if cls._is_year(token):
                return token
        return None

    @staticmethod
    def _normalise(text: str) -> str:
        """Lowercase and strip accents, so `España` and `espana` compare equal."""
        decomposed = unicodedata.normalize("NFKD", text or "")
        without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
        return " ".join(without_accents.lower().split())
