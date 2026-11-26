"""Prices from the search (plan step A7).

The shop has stock, not a market: most codes have one price or none. The search is
the second source, and it is a different kind of evidence — an asking price inside
a listing's snippet, with the condition guessed from its wording. That is why every
observation it produces says `kind: "ask"`, keeps the URL, and is only used when
the same condition has three of them.

The snippet carries the price but rarely the condition, and a price without a
condition cannot be averaged. So when the snippet is not enough, the listing page is
opened — only for hosts with a parser, only a few per query. A result without a price
is skipped, never counted as zero.
"""

from __future__ import annotations

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
from ai_api.sources.listings import parse as parse_listing, parser_for
from ai_api.text import condition_of, price_in as text_price_in
from common.log.logger import Logger


# Results walked per query: the first ones are the ones Google considered relevant.
MAX_RESULTS = 8

# Listing pages opened per query, and only for results the snippet could not
# finish: each one is a request of a few hundred KB.
MAX_PAGES = 3


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
        self,
        code: str,
        label: str = "",
        year: str = "",
        timeout: Optional[float] = None,
    ) -> List[Observation]:
        """Return the asking prices the search shows for one code.

        Args:
            code: the catalogue code, e.g. "2867".
            label: the series or stamp name, to narrow the query.
            year: the emission year, when it is known.
            timeout: seconds this call may take, when the caller has a budget.

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

        request_kwargs = {}
        if timeout is not None:
            request_kwargs["timeout"] = timeout

        response = self.client.post(
            self.url,
            json={"q": query, "gl": "es"},
            headers={"X-API-KEY": self.key},
            **request_kwargs,
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
        pages = 0

        for item in (results.get("organic") or [])[:MAX_RESULTS]:
            link = item.get("link") or ""
            if not self.client.is_allowed(link):
                continue

            text = f"{item.get('title') or ''} {item.get('snippet') or ''}"
            price = self.price_in(text)
            condition = condition_of(text)
            sold = False

            # The snippet gives a price and rarely a condition; the page gives
            # both. Only opened when the snippet is not enough, and only a few.
            if (price is None or condition == "unknown") and pages < MAX_PAGES:
                pages += 1
                listing = self._listing(link, timeout)
                if listing is not None:
                    price = listing.price if listing.price is not None else price
                    if listing.condition != "unknown":
                        condition = listing.condition
                    sold = listing.sold

            if price is None:
                continue

            observations.append(
                Observation(
                    source=self.name,
                    price=price,
                    kind="sold" if sold else "ask",
                    currency="EUR",
                    condition=condition,
                    url=link,
                    subject_code=code,
                    observed_at=datetime.now(timezone.utc),
                    raw={
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                    },
                )
            )

        self.log.debug(f"{self.name}: {len(observations)} price(s) for {code}")
        return observations

    def _listing(self, url: str, timeout: Optional[float] = None):
        """Open a listing page and read it, or None when it cannot be read."""
        if parser_for(url) is None:
            return None

        request_kwargs = {} if timeout is None else {"timeout": timeout}
        try:
            response = self.client.get(url, **request_kwargs)
        except SourceError as error:
            self.log.warning(f"{self.name}: could not open {url}: {error}")
            return None

        if response.status_code >= 400:
            self.log.warning(f"{self.name}: {url} answered {response.status_code}")
            return None

        try:
            return parse_listing(url, response.text)
        except Exception as error:  # a broken page is a gap, not a crash
            self.log.warning(f"{self.name}: could not parse {url}: {error}")
            return None

    @staticmethod
    def price_in(text: str) -> Optional[Decimal]:
        """Return the first price written in the text, or None."""
        return text_price_in(text)
