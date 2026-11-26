"""Small text helpers shared by the scraper and the catalogue adapter.

The description is what the model writes the stamp card from, so the rule lives
in one place: keep it whole unless it is unreasonably long.
"""

from __future__ import annotations

import re


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


# How a seller describes a condition, longest match first. "sin circular" means
# mint, so it has to be checked before the plain "circular".
CONDITION_RULES = (
    ("sin circular", "mnh"),
    ("sin charnela", "mnh"),
    ("sin fijasellos", "mnh"),
    ("sin usar", "mnh"),
    ("charnela", "mh"),
    ("fijasellos", "mh"),
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
