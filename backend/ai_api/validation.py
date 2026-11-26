"""Keep only what the sources support (plan step A9).

The model reads the catalogue facts and writes a JSON. It can also write a code, a
date or a print run the input never mentioned, and nothing in the contract can tell
those apart from the real ones. This module does: a field stays only when the facts
of the request back it, and the ones that do not are set to null and reported.

A value is not accepted because it looks right — that is the problem, not the
solution. Text is compared ignoring case, accents and spacing; numbers ignoring
their separators; a date written as `1986-11-16` matches `16 noviembre 1986`.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional

from ai_api.text import strip_html


# The series fields the checker looks at, and where each lives in the facts.
SERIES_FIELDS = {
    "issue_name": "issue_name",
    "issue_date": "issue_date",
    "artist": "engraver",
    "printer": "printer",
    "print_type": "print_type",
    "perforation": "perforation",
    "total_printed": "print_run",
}

# Fields no catalogue gives its own slot for (the shop's "Formato" is the size, not
# the type). They are not dropped outright: the value is kept when the source text
# mentions it somewhere — "Estucado" or "Hoja bloque" in a description is support.
FIELDS_FROM_THE_TEXT = ("paper_type", "stamp_type")

STAMP_FIELDS = (
    "edifil_code",
    "fesofi_code",
    "face_value",
    "motive",
    "color",
    "perforation",
    "total_print_run",
    "amount_printed",
)

# A payload with two hundred unsupported fields is not more useful for listing all
# of them.
MAX_GAPS = 20

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def check_support(data: Dict[str, Any], facts: Dict[str, Any]) -> List[dict]:
    """Null the fields of `data` that `facts` does not support.

    Args:
        data: the validated response, mutated in place.
        facts: `{"serie_info": {...}, "stamps": [...]}` as the sources returned it.

    Returns:
        One gap per removed field, with its name and why.
    """
    serie = (facts or {}).get("serie_info") or {}
    gaps: List[dict] = []

    for field, fact_key in SERIES_FIELDS.items():
        if field not in data:
            continue
        if not _supported(data.get(field), serie.get(fact_key)):
            data[field] = None
            gaps.append(_gap(field))

    haystack = _haystack(facts)
    for field in FIELDS_FROM_THE_TEXT:
        value = data.get(field)
        if value in (None, "", "n/a"):
            continue
        if _text(value) not in haystack:
            data[field] = None
            gaps.append(_gap(field))

    _check_stamps(data, (facts or {}).get("stamps") or [], gaps)

    return gaps[:MAX_GAPS]


def _check_stamps(data: Dict[str, Any], fact_stamps: List[dict], gaps: List[dict]) -> None:
    """Check the stamp rows against the facts, matching by code."""
    by_code = {
        _text(stamp.get("edifil_code")): stamp
        for stamp in fact_stamps
        if _text(stamp.get("edifil_code"))
    }
    by_fesofi = {
        _text(stamp.get("fesofi_code")): stamp
        for stamp in fact_stamps
        if _text(stamp.get("fesofi_code"))
    }

    for row in data.get("stamps") or []:
        if not isinstance(row, dict):
            continue

        fact = by_code.get(_text(row.get("edifil_code"))) or by_fesofi.get(
            _text(row.get("fesofi_code"))
        )

        if fact is None:
            # The code itself is not in the sources: an invented catalogue code is
            # the one mistake that looks most like data.
            for field in ("edifil_code", "fesofi_code"):
                if row.get(field) not in (None, ""):
                    row[field] = None
                    gaps.append(_gap(f"stamp.{field}"))
            continue

        for field in STAMP_FIELDS:
            if field not in row:
                continue
            fact_key = "fesofi_code" if field == "fesofi_code" else field
            if field == "amount_printed":
                fact_key = "total_print_run"
            if not _supported(row.get(field), fact.get(fact_key)):
                row[field] = None
                gaps.append(_gap(f"stamp.{field}"))


def _gap(field: str) -> dict:
    """One removed field, in the shape the response reports gaps."""
    return {"field": field, "reason": "No source supports this value."}


# ----------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------


def _supported(value: Any, fact: Any) -> bool:
    """True when the value matches the fact, in any of the ways we accept."""
    if value in (None, "", "n/a"):
        return True  # nothing claimed, nothing to check
    if fact in (None, "", "n/a"):
        return False

    if _number(value) is not None and _number(fact) is not None:
        return _number(value) == _number(fact)

    model_date = _as_date(value)
    if model_date is not None:
        fact_date = _as_date(fact)
        return fact_date is not None and model_date == fact_date

    return _text(value) in _text(fact) or _text(fact) in _text(value)


def _haystack(facts: Dict[str, Any]) -> str:
    """Every value the sources returned, as one text to search in."""
    parts: List[str] = []
    for value in ((facts or {}).get("serie_info") or {}).values():
        if value:
            parts.append(str(value))
    for stamp in (facts or {}).get("stamps") or []:
        for value in stamp.values():
            if value:
                parts.append(str(value))
    return _text(" ".join(parts))


def _text(value: Any) -> str:
    """Lowercase, no accents, no HTML, single spaces."""
    from ai_api.sources.store import StoreCatalogue  # one normaliser, not two

    return StoreCatalogue._normalise(strip_html(str(value or "")))


_NUMBER = re.compile(r"\d[\d.,]*")


def _number(value: Any) -> Optional[str]:
    """The digits of a number, without separators; None when it is not one."""
    text = str(value or "").strip()
    match = _NUMBER.fullmatch(text)
    if match is None:
        return None
    digits = re.sub(r"\D", "", match.group(0))
    return digits or None


def _as_date(value: Any) -> Optional[date]:
    """Read a date written as ISO or as `16 noviembre 1986`."""
    text = str(value or "").strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))

    words = _text(text).replace(",", " ").split()
    if len(words) != 3:
        return None

    day, month, year = words
    if month in MONTHS:
        pass
    elif day in MONTHS:  # "noviembre 16 1986"
        day, month = month, day
    else:
        return None

    if not (day.isdigit() and year.isdigit()):
        return None
    try:
        return date(int(year), MONTHS[month], int(day))
    except ValueError:
        return None
