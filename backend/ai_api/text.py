"""Small text helpers shared by the scraper and the catalogue adapter.

The description is what the model writes the stamp card from, so the rule lives
in one place: keep it whole unless it is unreasonably long.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional


# A guard against a pathological page, not a token diet: cutting a normal
# description saved a fraction of a cent and lost the best material the model has.
DESCRIPTION_LIMIT = 2000


def snippet(text: str) -> str:
    """Return the description, cut only when it is longer than the limit.

    The ellipsis is the model's only clue that the text is not complete, so it
    must not appear on a description that was not cut.
    """
    if not text:
        return "N/A"
    if len(text) <= DESCRIPTION_LIMIT:
        return text
    return text[:DESCRIPTION_LIMIT] + "…"


def strip_html(text: str) -> str:
    """Turn a fragment of HTML into readable text, whitespace collapsed."""
    without_tags = re.sub(r"<[^>]+>", " ", text or "")
    return " ".join(without_tags.split())


# How a seller describes a condition, most explicit first. "sin circular" and
# "sin fijasello" mean mint never hinged; "circular" and "fijasello" alone do not.
CONDITION_RULES = (
    ("mnh", "mnh"),
    ("sin circular", "mnh"),
    ("sin charnela", "mnh"),
    ("sin fijasello", "mnh"),
    ("sin usar", "mnh"),
    ("charnela", "mh"),
    ("fijasello", "mh"),
    ("usado", "used"),
    ("matasellad", "used"),
    ("circular", "used"),
    ("cto", "cto"),
)


def condition_of(text: str) -> str:
    """Map a listing's wording to the conditions the API speaks."""
    lowered = (text or "").lower()
    for needle, condition in CONDITION_RULES:
        if needle in lowered:
            return condition
    return "unknown"


# A price written after the currency ("12,50 €") or before it ("EUR 9,99"), with
# the Spanish thousand separator when there is one ("1.250,00 €").
_AMOUNT = r"(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
PRICE_AFTER = re.compile(rf"{_AMOUNT}\s*(?:€|eur\b)", re.IGNORECASE)
PRICE_BEFORE = re.compile(rf"(?:€|eur)\s*{_AMOUNT}", re.IGNORECASE)
_THOUSANDS_ONLY = re.compile(r"\d{1,3}(?:\.\d{3})+")


def price_in(text: str) -> Optional[Decimal]:
    """Read the first price in a text, or None.

    "1.250,00 €" is 1250.00 and not 1.25: the separator that repeats every three
    digits is a thousand, the other one is the decimal.
    """
    text = text or ""
    match = PRICE_AFTER.search(text) or PRICE_BEFORE.search(text)
    if match is None:
        return None

    token = match.group(1)
    if "," in token:
        token = token.replace(".", "").replace(",", ".")
    elif _THOUSANDS_ONLY.fullmatch(token):
        token = token.replace(".", "")

    return Decimal(token).quantize(Decimal("0.01"))
