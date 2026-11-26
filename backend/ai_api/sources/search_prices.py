"""Prices from the search (plan step A7).

The shop has stock, not a market: most codes have one price or none. The search is
the second source, and it is a different kind of evidence — an asking price inside
a listing's snippet, with the condition guessed from its wording. That is why every
observation it produces says `kind: "ask"`, keeps the URL, and is only used when
the same condition has three of them.

No page is fetched here: the snippet carries the price often enough, and reading
arbitrary marketplaces is its own step. A result without a price is skipped, never
counted as zero.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from django.conf import settings

from ai_api.sources.base import Observation
from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceError,
    SourceUnavailable,
)
from ai_api.sources.http import HttpClient, get_client
from ai_api.text import condition_of
from common.log.logger import Logger


# A price in a snippet, before the currency ("12,50 €") or after it ("EUR 12,50").
# Kept deliberately narrow: a wrong match is worse than a missed one.
PRICE_AFTER = re.compile(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:€|eur\b)", re.IGNORECASE)
PRICE_BEFORE = re.compile(r"(?:€|eur)\s*(\d{1,4}(?:[.,]\d{1,2})?)", re.IGNORECASE)

# Results walked per query: the first ones are the ones Google considered relevant.
MAX_RESULTS = 8


class SearchPrices(Logger):
    """Read asking prices from the search results of one catalogue code."""

    name = "search"

    def __init__(
        self,
        client: Optional[HttpClient] = None,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ) -> None:
        """Take the shared client; the backend comes from settings."""
        super().__init__()
        self.client = client or get_client()
        self.url = url if url is not None else settings.SERPER_URL
        self.key = key if key is not None else settings.SERPER_API_KEY

    def prices(
        self, code: str, label: str = "", year: str = ""
    ) -> List[Observation]:
        """Return the asking prices the search shows for one code.

        Args:
            code: the catalogue code, e.g. "2867".
            label: the series or stamp name, to narrow the query.
            year: the emission year, when it is known.

        Returns:
            One observation per result that carries a price. An empty list means
            the search had nothing usable, which is a gap.
        """
        if not self.url or not self.key:
            raise SourceConfigurationError(
                "The search backend is not configured: SERPER_URL and "
                "SERPER_API_KEY are required."
            )

        query = " ".join(part for part in (code, label, year, "sello") if part)
        self.log.debug(f"{self.name}: searching {query!r}")

        response = self.client.post(
            self.url,
            json={"q": query, "gl": "es"},
            headers={"X-API-KEY": self.key},
        )

        if response.status_code in (401, 403):
            raise SourceConfigurationError(
                f"The search backend refused the key (HTTP {response.status_code})."
            )
        if response.status_code >= 400:
            raise SourceUnavailable(
                f"The search backend answered HTTP {response.status_code}."
            )

        try:
            results = response.json()
        except ValueError as error:
            raise SourceError("The search backend did not answer JSON.") from error

        observations = []
        for item in (results.get("organic") or [])[:MAX_RESULTS]:
            observation = self._observation(item, code)
            if observation is not None:
                observations.append(observation)

        self.log.debug(f"{self.name}: {len(observations)} price(s) for {code}")
        return observations

    def _observation(self, item: dict, code: str) -> Optional[Observation]:
        """Turn one search result into an observation, if it is usable."""
        link = item.get("link") or ""
        if not self.client.is_allowed(link):
            return None

        text = f"{item.get('title') or ''} {item.get('snippet') or ''}"
        price = self.price_in(text)
        if price is None:
            return None

        return Observation(
            source=self.name,
            price=price,
            kind="ask",
            currency="EUR",
            condition=condition_of(text),
            url=link,
            subject_code=code,
            observed_at=datetime.now(timezone.utc),
            raw={"title": item.get("title"), "snippet": item.get("snippet")},
        )

    @staticmethod
    def price_in(text: str) -> Optional[Decimal]:
        """Return the first price written in the text, or None."""
        text = text or ""
        match = PRICE_AFTER.search(text) or PRICE_BEFORE.search(text)
        if match is None:
            return None
        return Decimal(match.group(1).replace(",", ".")).quantize(Decimal("0.01"))
