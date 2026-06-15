"""
Column definitions and formatters for the issue table.

Provides the ColumnDef dataclass used as the single source of truth
for all table columns, along with locale-aware formatters for
currency, number, and date display.

Shared module avoids circular imports between table components.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

import datetime
import flet as ft

from core.translations import _


@dataclass
class ColumnDef:
    """Definition for a single table column.

    Attributes:
        translation_key: Dot-notation key for the header label translation
            (e.g. "stamps.country", "ui.date").
        api_key: Key used in the API response dict (e.g. "country", "date").
        width: Fixed width in pixels. None means the column expands to fill
            remaining horizontal space.
        text_align: Text alignment within the cell (default LEFT).
        sortable: When True, clicking the header toggles sort by this column.
        fmt: Optional formatter function (value, lang) -> display string.
            Used for locale-aware rendering (currency, numbers, dates).
    """

    translation_key: str
    api_key: str
    width: Optional[int] = None
    text_align: ft.TextAlign = ft.TextAlign.LEFT
    sortable: bool = False
    fmt: Optional[Callable[[Any, str], str]] = None


def fmt_currency(value: Any, lang: str) -> str:
    """Format a monetary value with locale-aware separators; return "-" for zero.

    en: "€1,234.56"
    es: "€1.234,56"
    Returns "-" when value is 0, None, or empty.

    Args:
        value: Raw value (string or number). None/empty → "-".
        lang: Language code ("en" or "es").

    Returns:
        Formatted string with Euro symbol and two decimal places, or "-" for zero.
    """
    val: float = float(value or 0)
    if val == 0:
        return "-"
    formatted: str = f"€{val:,.2f}"
    if lang == "es":
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def fmt_number(value: Any, lang: str) -> str:
    """Format an integer with locale-aware thousands separator; return "-" for zero.

    en: "1,234,567"
    es: "1.234.567"
    Returns "-" when value is 0, None, or empty.

    Args:
        value: Raw value (string or number). None/empty → "-".
        lang: Language code ("en" or "es").

    Returns:
        Formatted integer string without decimals, or "-" for zero.
    """
    val: int = int(value or 0)
    if val == 0:
        return "-"
    formatted: str = f"{val:,}"
    if lang == "es":
        formatted = formatted.replace(",", ".")
    return formatted


def fmt_date(value: str, lang: str) -> str:
    """Format an ISO date string into a locale-aware display string.

    Month names come from locale JSON files (date.months.1-12)
    so they're fully translatable without hardcoding.

    en: "15 of June of 2023"
    es: "15 de junio de 2023"

    Args:
        value: ISO date string ("YYYY-MM-DD") or empty/null.
        lang: Language code. Passed for interface consistency with other
            formatters but unused internally (locale lookup via _()).

    Returns:
        Formatted date string, or "-" if empty, or raw value if unparseable.
    """
    if not value:
        return "-"
    try:
        dt = datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return value or "-"
    month_name: str = _(f"date.months.{dt.month}")
    of_word: str = _("common.of")
    return f"{dt.day} {of_word} {month_name} {of_word} {dt.year}"


# Single source of truth for all table columns.
# To add, remove, or reorder columns, edit this list —
# header and row components update automatically.
COLUMNS: list[ColumnDef] = [
    ColumnDef("common.country", "country", width=100),
    ColumnDef("ui.date", "date", width=120, sortable=True),
    ColumnDef("issues.name", "name", text_align=ft.TextAlign.LEFT, sortable=True),
    ColumnDef("common.artist", "artist"),
    ColumnDef("common.printer", "printer"),
    ColumnDef("common.perforation", "perforation", width=100),
    ColumnDef("common.stamp_type", "stamp_type", width=100),
    ColumnDef("common.print_type", "print_type", width=100),
    ColumnDef("common.paper_type", "paper_type", width=100),
    ColumnDef("stamps.total_printed", "total_printed", width=120, text_align=ft.TextAlign.RIGHT, fmt=fmt_number),
    ColumnDef("ui.value", "market_value_mnh", width=100, text_align=ft.TextAlign.RIGHT, fmt=fmt_currency),
]