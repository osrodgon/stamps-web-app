"""
Column definition and formatters for the issue table.

Shared module to avoid circular imports between table components.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

import flet as ft

from core.translations import _

@dataclass
class ColumnDef:
    """Definition for a single table column.

    Attributes:
        translation_key: Key for the header label translation.
        api_key: Key used in the API response dict.
        width: Column width in pixels (None = expand to fill space).
        text_align: Text alignment within the cell.
        sortable: Whether clicking the header sorts by this column.
        fmt: Optional formatter (value, lang) -> display string.
    """
    translation_key: str
    api_key: str
    width: Optional[int] = None
    text_align: ft.TextAlign = ft.TextAlign.LEFT
    sortable: bool = False
    fmt: Optional[Callable[[Any, str], str]] = None


def fmt_currency(value: Any, lang: str) -> str:
    """Format a monetary value with locale-aware separators."""
    val: float = float(value or 0)
    formatted: str = f"€{val:,.2f}"
    if lang == "es":
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def fmt_number(value: Any, lang: str) -> str:
    """Format an integer with locale-aware thousands separator."""
    val: int = int(value or 0)
    formatted: str = f"{val:,}"
    if lang == "es":
        formatted = formatted.replace(",", ".")
    return formatted

import datetime


def fmt_date(value: str, lang: str) -> str:
    """
    Format an ISO date string (YYYY-MM-DD) into a locale-aware display string.

    en: "15 of June of 2023"
    es: "15 de junio de 2023"
    """
    if not value:
        return "-"
    try:
        dt = datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return value or "-"
    if lang == "es":
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        return f"{dt.day} {_('ui.of')} {months[dt.month - 1]} {_('ui.of')} {dt.year}"
    months_en = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    return f"{dt.day} {_('ui.of')} {months_en[dt.month - 1]} {_('ui.of')} {dt.year}"


# Single source of truth for all table columns.
# To add/remove/reorder columns, edit this list — header and rows update automatically.
COLUMNS: list[ColumnDef] = [
    ColumnDef("stamps.country", "country", width=100),
    ColumnDef("ui.date", "date", width=120, sortable=True),
    ColumnDef("stamps.issue_name", "name", text_align=ft.TextAlign.LEFT, sortable=True), 
    ColumnDef("stamps.artist", "artist"),
    ColumnDef("stamps.printer", "printer"),
    ColumnDef("stamps.perforation", "perforation", width=100),
    ColumnDef("stamps.stamp_type", "stamp_type", width=100),
    ColumnDef("stamps.print_type", "print_type", width=100),
    ColumnDef("stamps.paper_type", "paper_type", width=100),
    ColumnDef("stamps.total_printed", "total_printed", width=120, text_align=ft.TextAlign.RIGHT, fmt=fmt_number),
    ColumnDef("ui.value", "market_value_mnh", width=100, text_align=ft.TextAlign.RIGHT, fmt=fmt_currency)
]
