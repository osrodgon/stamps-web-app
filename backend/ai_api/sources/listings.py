"""Reading a listing page, where the condition actually is (plan step A7b).

The search gives a price and no condition; the shop gives a condition and hardly
any stock. The listing page has both, and each site says it its own way, so this
module is one parser per site behind one shape.

Only `todocoleccion.net` is parsed: eBay answers 403 (an error page, not a
challenge) to a client that is not a browser, so its links stay snippet-only until
there is a way in that is not a headless browser.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bs4 import BeautifulSoup

from ai_api.text import condition_of, price_in



# A page that says it was sold is a sale, not an asking price.
SOLD = re.compile(r"\bvendido\b", re.IGNORECASE)


@dataclass(frozen=True)
class Listing:
    """What a listing page says, in the terms the rest of the API uses."""

    price: Optional[Decimal] = None
    condition: str = "unknown"
    title: str = ""
    sold: bool = False


class ListingParser(ABC):
    """One site's way of writing a listing."""

    name: str = ""
    host: str = ""

    @abstractmethod
    def parse(self, html: str) -> Listing:
        """Read the price and the condition out of one listing page."""


class TodoColeccionParser(ListingParser):
    """`todocoleccion.net`: the price in `lote-precio`, the condition in the title.

    The "Estado del lote" line describes wear ("Muy Bueno", "Normal"), not mint
    against used, so it is not used as a condition: the title is, because that is
    where a seller writes "NUEVO MNH** sin fijasello" or "Usado".
    """

    name = "todocoleccion"
    host = "todocoleccion.net"

    def parse(self, html: str) -> Listing:
        soup = BeautifulSoup(html or "", "html.parser")

        title_node = soup.select_one("h1#lote-page-h1") or soup.find("h1")
        title = " ".join(title_node.get_text(" ", strip=True).split()) if title_node else ""

        price_node = soup.select_one("span.lote-precio")
        price = self._price(price_node.get_text(" ", strip=True) if price_node else "")

        text = " ".join(soup.get_text(" ", strip=True).split())
        sold = bool(SOLD.search(text))

        return Listing(
            price=price,
            condition=condition_of(title),
            title=title,
            sold=sold,
        )

    @staticmethod
    def _price(text: str) -> Optional[Decimal]:
        """Read the price of the listing, or None when the page does not show it."""
        return price_in(text)


PARSERS = (TodoColeccionParser(),)


def parser_for(url: str) -> Optional[ListingParser]:
    """Return the parser that understands this host, or None."""
    lowered = (url or "").lower()
    for parser in PARSERS:
        if parser.host and parser.host in lowered:
            return parser
    return None


def parse(url: str, html: str) -> Optional[Listing]:
    """Parse a page with the right parser, if there is one."""
    parser = parser_for(url)
    if parser is None:
        return None
    return parser.parse(html)
