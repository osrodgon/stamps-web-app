"""
Column definition and formatters for the issue table.

Shared module to avoid circular imports between table components.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

import flet as ft

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
