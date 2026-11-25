"""Helpers for the A0 source probe of the AI extraction plan.

The A0 step (`memory-bank/ai-api-plan.md`) answers, for each external source,
three questions: is it reachable from this host, what shape does it return, and
may we use it according to ``robots.txt``. This module holds the pure parts —
subjects, URL builders, parsers, markers and the robots check — so they can be
tested without network access. The I/O lives in the ``ai_sources_probe``
management command.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

USER_AGENT = "stamps-web-app-probe/0.1 (+https://github.com/oscarro/stamps-web-app)"

DEFAULT_TIMEOUT = 25


@dataclass(frozen=True)
class Subject:
    """One real series to probe the sources with.

    The five defaults are rows of the production database on 2026-11-25,
    picked to span the catalogue: a classic (1850), two 1928-1930 series, the
    longest series (57 stamps, 1992) and a modern one (1998). They are meant to
    exercise the sources, not to prove a match — that is A6's job.
    """

    issue_id: int
    name: str
    year: int
    first_edifil: str
    first_fesofi: str
    stamps: int

    @property
    def query(self) -> str:
        """Text a matcher would search for: the catalogue code and the year."""
        return f"{self.first_edifil} {self.year}"

    def as_dict(self) -> Dict[str, Any]:
        """Serialize the subject for the probe report."""
        return asdict(self)


SUBJECTS: tuple[Subject, ...] = (
    Subject(
        issue_id=2551,
        name="Isabel II",
        year=1850,
        first_edifil="1",
        first_fesofi="0001",
        stamps=5,
    ),
    Subject(
        issue_id=71,
        name="Pro Catacumbas de San Dámaso",
        year=1928,
        first_edifil="402",
        first_fesofi="0402",
        stamps=32,
    ),
    Subject(
        issue_id=81,
        name="Quinta de Goya en la Exposición de Sevilla",
        year=1930,
        first_edifil="517",
        first_fesofi="0517",
        stamps=14,
    ),
    Subject(
        issue_id=842,
        name="Expo 92 Sevilla",
        year=1992,
        first_edifil="3164",
        first_fesofi="3196",
        stamps=57,
    ),
    Subject(
        issue_id=1010,
        name="Correspondencia epistolar escolar",
        year=1998,
        first_edifil="3560",
        first_fesofi="1998026",
        stamps=27,
    ),
)

COLNECT_ROBOTS = "https://colnect.com/robots.txt"
COLNECT_CAPI = "https://api.colnect.net/en/api/{app_id}/categories"
COLNECT_PUBLIC = "https://colnect.com/en/stamps/list/country/67-Spain/year/{year}"
DELCAMPE_ROBOTS = "https://www.delcampe.net/robots.txt"
# The search form on the home page posts `term`, not `q`: with `q` Delcampe
# ignores the text and serves the default browse page (checked 2026-11-25).
DELCAMPE_SEARCH = "https://www.delcampe.net/en_GB/collectables/search?term={query}"
DELCAMPE_SEARCH_PATH = "/en_GB/collectables/search"
IBERPHIL_ROBOTS = "https://www.iberphil.com/robots.txt"
IBERPHIL_HOME = "https://www.iberphil.com/es/"
IBERPHIL_HISTORY = "https://www.iberphil.com/es/subastas-historico"
FESOFI_HOME = "https://catalogodesellos.fesofi.es/"
# The WooCommerce Store API answers JSON without a key; `sku` is an exact match,
# while `search` is a fuzzy full-text one that also returns the FDC sheets.
FESOFI_STORE_API = (
    "https://catalogodesellos.fesofi.es/wp-json/wc/store/v1/products"
    "?sku={code}&per_page=3"
)


def delcampe_search_url(subject: Subject) -> str:
    """Build the Delcampe search URL for a subject."""
    return DELCAMPE_SEARCH.format(query=quote_plus(subject.query))


def colnect_public_url(subject: Subject) -> str:
    """Build the public Colnect list URL for a subject's year."""
    return COLNECT_PUBLIC.format(year=subject.year)


def colnect_capi_url(app_id: str = "000000") -> str:
    """Build a CAPI URL with the given app id (a placeholder probes the 401)."""
    return COLNECT_CAPI.format(app_id=app_id)


def fesofi_search_url(subject: Subject) -> str:
    """Build the WooCommerce Store API lookup URL for a subject's Fesofi code."""
    return FESOFI_STORE_API.format(code=quote_plus(subject.first_fesofi))


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------


def _robots_groups(text: str) -> Dict[str, List[tuple[str, str]]]:
    """Split a robots.txt into ``{agent: [(allow|disallow, pattern), ...]}``."""
    groups: Dict[str, List[tuple[str, str]]] = {}
    agents: List[str] = []
    last_was_agent = False

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue

        field, value = (part.strip() for part in line.split(":", 1))
        field = field.lower()

        if field == "user-agent":
            if not last_was_agent:
                agents = []
            agents.append(value.lower())
            last_was_agent = True
            for agent in agents:
                groups.setdefault(agent, [])
            continue

        if field in ("allow", "disallow"):
            last_was_agent = False
            for agent in agents:
                groups[agent].append((field, value))
        else:
            last_was_agent = False

    return groups


def _rule_matches(pattern: str, path: str) -> bool:
    """Return True when a robots.txt pattern matches the path."""
    if pattern in ("", "/") and pattern == "":
        return False

    regex = re.escape(pattern).replace(r"\*", ".*")
    anchored = pattern.endswith("$")
    if anchored:
        regex = regex[:-2] if regex.endswith(r"\$") else regex
        regex = regex.rstrip("$")

    expression = f"^{regex}{'$' if anchored else ''}"
    return re.match(expression, path) is not None


def robots_rule(robots_text: str, path: str, user_agent: str = USER_AGENT) -> Optional[str]:
    """Return the robots.txt rule that decides for ``path``, or None if allowed.

    The most specific matching group is used (a named agent before ``*``), and
    inside a group the longest pattern wins, with ``Allow`` winning a tie.
    """
    groups = _robots_groups(robots_text)
    token = user_agent.lower().split("/")[0]

    named = [agent for agent in groups if agent != "*" and agent and agent in token]
    chosen: List[tuple[str, str]] = []
    if named:
        for agent in named:
            chosen.extend(groups[agent])
    else:
        chosen = groups.get("*", [])

    best: Optional[tuple[str, str]] = None
    for kind, pattern in chosen:
        if not _rule_matches(pattern, path):
            continue
        if best is None or len(pattern) > len(best[1]):
            best = (kind, pattern)
        elif len(pattern) == len(best[1]) and kind == "allow":
            best = (kind, pattern)

    if best is None or best[0] == "allow":
        return None
    return f"Disallow: {best[1]}"


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


CHALLENGE_MARKERS: tuple[tuple[str, str], ...] = (
    ("anubis", "within.website"),
    ("anubis", "collectors protection"),
    ("cloudflare", "cf-browser-verification"),
    ("cloudflare", "just a moment"),
    ("cloudflare", "attention required"),
    ("captcha", "g-recaptcha"),
    ("captcha", "hcaptcha"),
)


def detect_challenge(html: str) -> Optional[str]:
    """Name the bot challenge in an HTML body, or None when there is none."""
    lowered = html.lower()
    for name, marker in CHALLENGE_MARKERS:
        if marker in lowered:
            return name
    return None


def response_shape(content_type: str, body: bytes) -> str:
    """Describe what came back: ``html``, ``json``, ``xml``, ``binary`` or ``empty``."""
    if not body:
        return "empty"
    content_type = (content_type or "").lower()
    if "json" in content_type:
        return "json"
    if "html" in content_type:
        return "html"
    if "xml" in content_type:
        return "xml"
    if content_type.startswith("text/"):
        return "text"
    return "binary"


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_delcampe_cards(html: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Extract listing cards from a Delcampe search page."""
    soup = BeautifulSoup(html, "html.parser")
    cards: List[Dict[str, Any]] = []

    for link in soup.select("a.item-link[href]"):
        title_node = link.select_one("h2.item-title")
        if title_node is None:
            continue
        card = link.find_parent("div", id=re.compile(r"^item-"))
        price_node = card.select_one("strong.item-price") if card else None
        selling = card.select_one(".selling-type[title]") if card else None
        cards.append(
            {
                "title": " ".join(title_node.get_text(" ", strip=True).split()),
                "url": link.get("href"),
                "price": price_node.get_text(strip=True) if price_node else None,
                "selling_type": selling.get("title") if selling else None,
            }
        )
        if len(cards) >= limit:
            break

    return cards


def parse_fesofi_products(payload: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Read the interesting fields of a WooCommerce Store API product list."""
    try:
        products = json.loads(payload)
    except (TypeError, ValueError):
        return []
    if not isinstance(products, list):
        return []

    rows: List[Dict[str, Any]] = []
    for product in products[:limit]:
        attributes = {
            attribute.get("name"): ", ".join(
                term.get("name", "") for term in attribute.get("terms", [])
            )
            for attribute in product.get("attributes", [])
        }
        rows.append(
            {
                "name": product.get("name"),
                "sku": product.get("sku"),
                "permalink": product.get("permalink"),
                "price": (product.get("prices") or {}).get("price"),
                "currency": (product.get("prices") or {}).get("currency_code"),
                "attributes": attributes,
            }
        )
    return rows


def parse_iberphil_sold_lots(html: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Extract the rows of an ``auction-sold-lots`` table."""
    soup = BeautifulSoup(html, "html.parser")
    rows: List[Dict[str, Any]] = []

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers or "lote" not in headers[0].lower():
            continue
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(cells) < len(headers):
                continue
            rows.append(dict(zip(headers, cells)))
            if len(rows) >= limit:
                return rows

    return rows


def parse_iberphil_lot(html: str) -> Dict[str, Any]:
    """Read the prices and the description of one Iberphil lot page.

    A closed lot shows ``Puja inicial`` (or ``Libre``) and ``Adjudicación``, the
    hammer price: ``0€`` means it did not sell. The page carries no catalogue
    code, so ``mentions_edifil`` is the only link a matcher could use.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())

    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"]

    starting = _price_after(text, "Puja inicial")
    hammer = _price_after(text, "Adjudicación")
    free_start = "Puja inicial Libre" in text
    haystack = f"{text} {description}".lower()

    return {
        "description": description[:300],
        "starting_price": starting,
        "starting_free": free_start,
        "hammer_price": hammer,
        "sold": bool(hammer and hammer not in ("0", "0,00", "0.00")),
        "mentions_edifil": "edifil" in haystack,
        "mentions_fesofi": "fesofi" in haystack,
    }


def parse_iberphil_lot_links(html: str, limit: int = 5) -> List[str]:
    """Return the lot URLs linked from a sold-lots page."""
    soup = BeautifulSoup(html, "html.parser")
    found: List[str] = []

    for link in soup.select("a[href]"):
        href = link.get("href")
        if not href or "/lote-" not in href:
            continue
        if href not in found:
            found.append(href)
        if len(found) >= limit:
            break

    return found


def _price_after(text: str, label: str) -> Optional[str]:
    """Return the first price-looking token after a label."""
    match = re.search(re.escape(label) + r"[^\d]{0,40}(\d[\d.]*[,.]?\d*)\s*€", text)
    return match.group(1) if match else None


def parse_iberphil_auctions(html: str, limit: int = 3) -> List[str]:
    """Return the first auction paths linked from the history page."""
    soup = BeautifulSoup(html, "html.parser")
    found: List[str] = []

    for link in soup.select("a[href]"):
        href = link.get("href")
        if not href or "/subastas-sellos/" not in href:
            continue
        if href.rstrip("/").endswith(("historico", "subastas-sellos")):
            continue
        path = href.split("?")[0].rstrip("/")
        if path not in found:
            found.append(path)
        if len(found) >= limit:
            break

    return found


def parse_iberphil_first_lot(html: str) -> Optional[str]:
    """Return the first lot URL of a page, if it links one."""
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        href = link.get("href")
        if href and "/lote-" in href:
            return href
    return None


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------


def verdict(status: Optional[int], challenge: Optional[str], error: Optional[str] = None) -> str:
    """One-line reading of a probe result, to be printed and stored."""
    if error:
        return f"unreachable: {error}"
    if challenge:
        return f"blocked by a bot challenge ({challenge})"
    if status == 426:
        return "rejected: HTTP/2 required by the server"
    if status == 401:
        return "reachable, credentials required (401)"
    if status == 403:
        return "reachable, access denied for this client (403)"
    if status and 200 <= status < 300:
        return "reachable"
    if status == 404:
        return "not found (404)"
    if status and status >= 500:
        return f"server error ({status})"
    return f"unexpected status {status}"
