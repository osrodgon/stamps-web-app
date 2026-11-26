"""The WooCommerce Store API, shared by every catalogue we read (plan step A7).

Fesofi and `filatelia.online` are the same shop software: `/products`, its
attributes as terms and products with `attributes`, `prices` and `permalink`. What
changes is the base URL, the language and which attribute means what, so the HTTP,
the term search and the text comparison live here once.

Nothing in this module knows what a stamp is; `fesofi.py` does the identity and
`filatelia.py` the prices.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set

from ai_api.sources.errors import SourceError, SourceUnavailable
from ai_api.sources.http import HttpClient, get_client
from common.log.logger import Logger


# Words that carry no identity: without this, "Castillos de España" would never
# match "Castillos de España" because of the "de".
STOPWORDS = frozenset(
    {
        "de", "del", "la", "el", "los", "las", "y", "e", "en", "a", "al",
        "con", "por", "para", "un", "una", "unos", "unas", "serie", "sello",
        "sellos", "hoja", "bloque", "emision", "emisión",
    }
)


class StoreCatalogue(Logger):
    """Read one WooCommerce store through its public Store API.

    Attributes:
        name: identifier of the store, the same string observations carry.
        root: API root, e.g. `https://…/wp-json/wc/store/v1`.
    """

    name: str = ""
    root: str = ""

    def __init__(self, client: Optional[HttpClient] = None) -> None:
        """Take the shared HTTP client, or the one a test injects."""
        super().__init__()
        self.client = client or get_client()
        # Optional ceiling for every call this catalogue makes, set by a caller
        # with a budget (A8).
        self.timeout: Optional[float] = None

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def _terms(self, attribute: int, word: str, timeout: Optional[float] = None) -> List[dict]:
        """Return the terms of one attribute whose name contains `word`."""
        return self._list(
            f"{self.root}/products/attributes/{attribute}/terms",
            {"search": word, "per_page": 100},
            timeout,
        )

    def _term_id(
        self, attribute: int, text: str, timeout: Optional[float] = None
    ) -> Optional[int]:
        """Return the term id whose name is exactly `text`, or None."""
        wanted = self._normalise(text)
        for term in self._list(
            f"{self.root}/products/attributes/{attribute}/terms",
            {"search": text, "per_page": 10},
            timeout,
        ):
            if self._normalise(term.get("name", "")) == wanted:
                return int(term["id"])
        return None

    def _products(
        self,
        term: dict,
        filters: Optional[List[tuple]] = None,
        timeout: Optional[float] = None,
    ) -> List[dict]:
        """Return the products of one term, plus any attribute filters.

        Args:
            term: the term dict, with `taxonomy` and `id`.
            filters: extra `(taxonomy, term_id)` pairs, e.g. the year.
        """
        params: Dict[str, str] = {
            "attributes[0][attribute]": term["taxonomy"],
            "attributes[0][term_id]": str(term["id"]),
            "per_page": "100",
        }
        for index, (taxonomy, term_id) in enumerate(filters or [], start=1):
            params[f"attributes[{index}][attribute]"] = taxonomy
            params[f"attributes[{index}][term_id]"] = str(term_id)

        return self._list(f"{self.root}/products", params, timeout)

    def _list(
        self, url: str, params: Dict[str, str], timeout: Optional[float] = None
    ) -> List[dict]:
        """GET a Store API list, or say what went wrong."""
        request_kwargs: Dict[str, Any] = {"params": params}
        limit = timeout if timeout is not None else self.timeout
        if limit is not None:
            request_kwargs["timeout"] = limit

        response = self.client.get(url, **request_kwargs)

        if response.status_code >= 400:
            raise SourceUnavailable(
                f"{self.name} answered HTTP {response.status_code} for {url}."
            )

        try:
            data = response.json()
        except ValueError as error:
            raise SourceError(f"{self.name} did not answer JSON.") from error

        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    @classmethod
    def _attributes(cls, product: Dict[str, Any]) -> Dict[str, str]:
        """Flatten a product's attributes into ``{normalised name: value}``.

        The catalogue writes "Fecha De Emisión" with a capital D and "Año de
        Emisión" without it, so a key compared literally is a key that is missing.
        """
        return {
            cls._normalise(attribute.get("name", "")): ", ".join(
                term.get("name", "") for term in attribute.get("terms") or []
            )
            for attribute in product.get("attributes") or []
        }

    @staticmethod
    def _price(product: Dict[str, Any]) -> Optional[float]:
        """Return the product's price in major units, or None.

        The Store API sends minor units: `"price": "1000"` with
        `currency_minor_unit: 2` is 10.00 €, not 1.000 €.
        """
        prices = product.get("prices") or {}
        raw = prices.get("price")
        if raw in (None, ""):
            return None
        try:
            amount = int(raw)
        except (TypeError, ValueError):
            return None
        minor = int(prices.get("currency_minor_unit") or 0)
        return amount / (10 ** minor)

    @staticmethod
    def _currency(product: Dict[str, Any]) -> str:
        """Return the ISO code the product is priced in."""
        return (product.get("prices") or {}).get("currency_code") or "EUR"

    @staticmethod
    def _order(stamp: Dict[str, Any]) -> tuple:
        """Sort by catalogue code, the short one first, like the list order does."""
        code = str(stamp.get("edifil_code") or stamp.get("fesofi_code") or "")
        digits = re.sub(r"\D", "", code)
        return (len(digits), digits) if digits else (99, code)

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    @classmethod
    def _words(cls, name: str, keep_years: bool = False) -> List[str]:
        """Split a name into comparable words, dropping stopwords.

        A year in what the caller asked is a filter, so it is dropped there; a
        year inside a series name ("Navidad 2018") is part of that name and must
        stay, which is what `keep_years` does.
        """
        words = []
        for token in cls._normalise(name).split():
            token = token.strip(".,;:()[]«»\"'¡!¿?")
            if not token or token in STOPWORDS:
                continue
            if not keep_years and cls._is_year(token):
                continue
            words.append(token)
        return words

    @classmethod
    def _word_set(cls, name: str) -> Set[str]:
        """The words of a series name, years included."""
        return set(cls._words(name, keep_years=True))

    @classmethod
    def _coverage(cls, query: Set[str], name: str) -> int:
        """How many of the asked words the series name contains."""
        return len(query & cls._word_set(name))

    @classmethod
    def _is_exact(cls, query: Set[str], name: str) -> bool:
        """True when the series name is the asked words and nothing else."""
        return cls._word_set(name) == query

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
