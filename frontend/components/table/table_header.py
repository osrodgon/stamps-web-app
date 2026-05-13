"""
Table header component for the issue table.

Provides column titles with sort indicators aligned to data columns.
"""

from typing import Callable, Optional

import flet as ft

from components.colors import HEADER_BG
from components.table.column_def import ColumnDef
from core.translations import _


class TableHeader(ft.Container):
    """Column header row with sort controls.

    Builds header cells from a list of ColumnDef. Sortable columns
    display an arrow icon and toggle sort on click.
    """

    def __init__(
        self,
        columns: list[ColumnDef],
        sort_key: str = "date",
        sort_order: str = "asc",
        on_sort: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Initialize the table header with column definitions and sort state.

        Builds the header row by iterating COLUMNS. Sortable columns
        display an arrow icon and respond to clicks.

        Args:
            columns: List of ColumnDef driving header cells and behavior.
            sort_key: Currently sorted column API key.
            sort_order: Current sort direction ("asc" or "desc").
            on_sort: Called with (sort_key, sort_order) on header click.
        """
        super().__init__()
        self._columns: list[ColumnDef] = columns
        self._sort_key: str = sort_key
        self._sort_order: str = sort_order
        self._on_sort: Optional[Callable[[str, str], None]] = on_sort

        self._sort_icon: ft.Icon = ft.Icon(
            icon=ft.Icons.ARROW_DOWNWARD,
            size=14,
            color=ft.Colors.WHITE,
        )

        self.bgcolor = HEADER_BG
        self.padding = ft.Padding.symmetric(horizontal=10, vertical=8)
        self.height=50
        self._rebuild()

    def _rebuild(self) -> None:
        """Recreate all header controls."""
        self.content = ft.Row(
            controls=self._build_columns(),
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_columns(self) -> list[ft.Control]:
        """Build the header column list from COLUMNS definition."""
        cells: list[ft.Control] = [ft.Container(width=32)]

        for col in self._columns:
            if col.sortable:
                cells.append(self._build_sortable_column(col))
            else:
                cells.append(self._header_cell(
                    _(col.translation_key).upper(),
                    width=col.width,
                    text_align=col.text_align,
                ))

        cells.append(ft.Container(width=32))
        return cells

    def _header_cell(
        self,
        label: str,
        width: Optional[int] = None,
        text_align: ft.TextAlign = ft.TextAlign.LEFT,
    ) -> ft.Container:
        """Create a header label cell."""
        kwargs: dict = {}
        if width is None:
            kwargs["expand"] = True
        else:
            kwargs["width"] = width
        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                font_family="Roboto-Bold",
                color=ft.Colors.WHITE,
                text_align=text_align,
            ),
            **kwargs,
        )

    def _build_sortable_column(self, col: ColumnDef) -> ft.Container:
        """Build a sortable column header with icon and click handler."""
        is_active: bool = col.api_key == self._sort_key
        kwargs: dict = {}
        if col.width is None:
            kwargs["expand"] = True
        else:
            kwargs["width"] = col.width
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        _(col.translation_key).upper(),
                        size=12,
                        font_family="Roboto-Bold",
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(
                        content=self._sort_icon,
                        visible=is_active,
                    ),
                ],
                spacing=4,
            ),
            on_click=lambda e, k=col.api_key: self._toggle_sort(k),
            **kwargs,
        )

    def _toggle_sort(self, sort_key: str) -> None:
        """Toggle sort order and notify parent."""
        if sort_key == self._sort_key:
            self._sort_order = "desc" if self._sort_order == "asc" else "asc"
        else:
            self._sort_key = sort_key
            self._sort_order = "asc"

        self._sort_icon.icon = (
            ft.Icons.ARROW_UPWARD
            if self._sort_order == "asc"
            else ft.Icons.ARROW_DOWNWARD
        )

        self._rebuild()
        self.update()

        if self._on_sort:
            self._on_sort(self._sort_key, self._sort_order)

    def update_sort_indicators(self, sort_key: str, sort_order: str) -> None:
        """Update sort state from parent (e.g., after API call)."""
        self._sort_key = sort_key
        self._sort_order = sort_order
        self._sort_icon.icon = (
            ft.Icons.ARROW_UPWARD
            if sort_order == "asc"
            else ft.Icons.ARROW_DOWNWARD
        )
        self._rebuild()
        self.update()
