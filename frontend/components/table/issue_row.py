"""
Issue row component for the issue table.

Provides a single row displaying stamp issue data with expandable details.
"""

from typing import Callable, Optional

import flet as ft
from vine import wrap

from components.colors import (
    BG_LIGHT,
    DARK_BLUE_GREY,
    DELETE_RED,
    EXPANSION_BG,
    ICON_GREY,
    ROW_BORDER,
    ROW_HOVER,
    TEXT_BLUE,
)
from components.table.column_def import ColumnDef, fmt_currency
from core.translations import _


class IssueRow(ft.Container):
    """A single row in the issue table with expandable details.

    Builds data cells by iterating a list of ColumnDef, applying
    locale-aware formatting where configured.
    """

    def __init__(
        self,
        issue: dict,
        row_index: int = 0,
        columns: Optional[list[ColumnDef]] = None,
        lang: str = "en",
        on_expand: Optional[Callable[[int], None]] = None,
    ) -> None:
        super().__init__()
        self._issue: dict = issue
        self._row_index: int = row_index
        self._columns: list[ColumnDef] = columns or []
        self._lang: str = lang
        self._on_expand: Optional[Callable[[int], None]] = on_expand
        self._is_expanded: bool = False
        self._original_bgcolor: str | None = BG_LIGHT if row_index % 2 == 0 else None

        self._chevron_icon: ft.Icon = ft.Icon(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            size=16,
            color=ft.Colors.WHITE,
        )
        self._details: ft.Container = ft.Container(visible=False)

        self.content = ft.Column(
            controls=[self._build_main_row(), self._details],
            spacing=0,
        )
        self.bgcolor = self._original_bgcolor
        self.on_hover = self._on_hover

    def _build_main_row(self) -> ft.Container:
        """Build the visible row with chevron, data columns, and delete."""
        cells: list[ft.Control] = [self._build_chevron()]

        for col in self._columns:
            raw: str = self._issue.get(col.api_key, "")
            display: str = col.fmt(raw, self._lang) if col.fmt else (raw or "-")
            is_name: bool = col.api_key == "name"
            cells.append(self._cell(
                display,
                width=col.width,
                text_align=col.text_align,
                color=TEXT_BLUE if is_name else None,
            ))

        cells.append(self._build_delete_button())

        return ft.Container(
            content=ft.Row(
                controls=cells,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            border=ft.Border.only(bottom=ft.BorderSide(1, ROW_BORDER)),
        )

    def _build_chevron(self) -> ft.Container:
        """Circular blue button that toggles the details expansion."""
        return ft.Container(
            content=self._chevron_icon,
            width=24,
            height=24,
            bgcolor=DARK_BLUE_GREY,
            border_radius=16,
            alignment=ft.Alignment.CENTER,
            on_click=self._toggle_expand,
        )

    def _cell(
        self,
        text: str,
        width: Optional[int] = None,
        color: Optional[str] = None,
        text_align: ft.TextAlign = ft.TextAlign.LEFT,
    ) -> ft.Container:
        """Create a single data cell with fixed width or flexible expansion."""
        kwargs: dict = {}
        if width is None:
            kwargs["expand"] = True
        else:
            kwargs["width"] = width
        return ft.Container(
            content=ft.Text(
                text,
                size=14,
                color=color,
                font_family="Roboto",
                text_align=text_align,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            tooltip=text,
            **kwargs,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _build_delete_button(self) -> ft.Container:
        """Red circular delete button.

        TODO: Implement delete with AlertDialog confirmation.
        """
        return ft.Container(
            content=ft.Icon(
                icon=ft.Icons.DELETE,
                size=18,
                color=ft.Colors.WHITE,
            ),
            width=32,
            height=32,
            bgcolor=DELETE_RED,
            border_radius=4,
            alignment=ft.Alignment.CENTER,
        )

    def _build_details(self) -> ft.Container:
        """Hidden details panel shown when the chevron is clicked."""
        issue: dict = self._issue
        used: float = float(issue.get("market_value_used", 0) or 0)

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Description
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{_('ui.description')}:",
                                size=14,
                                font_family="Roboto-Bold",
                            )
                        ],
                        spacing=20,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{issue.get('description', '-')}",
                                size=14,
                                font_family="Roboto",
                            ),
                        ],
                        spacing=20,
                        wrap=True,
                        margin= ft.Margin(bottom=10)
                    ),
                    # Notes
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{_('ui.notes')}:",
                                size=14,
                                font_family="Roboto-Bold",
                            )
                        ],
                        spacing=20,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{issue.get('note', '-')}",
                                size=14,
                                font_family="Roboto",
                            ),
                        ],
                        spacing=20,
                        wrap=True,
                        margin= ft.Margin(bottom=10)
                    ),
                    # Market value used
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{_('stamps.market_value_used')}:",
                                size=14,
                                font_family="Roboto-Bold",
                            ),
                            ft.Text(
                                fmt_currency(used, self._lang),
                                size=14,
                                font_family="Roboto",
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.Padding.only(left=52, top=8, bottom=8),
            bgcolor=EXPANSION_BG,
            border=ft.Border.only(
                top=ft.BorderSide(1, ROW_BORDER),
                bottom=ft.BorderSide(1, ROW_BORDER),
            ),
        )

    def _toggle_expand(self, e: ft.ControlEvent) -> None:
        """Toggle the details section visibility."""
        self._is_expanded = not self._is_expanded

        self._chevron_icon.icon = (
            ft.Icons.KEYBOARD_ARROW_UP
            if self._is_expanded
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )

        if self._is_expanded:
            self._details.content = self._build_details()
        self._details.visible = self._is_expanded
        self.update()

        if self._on_expand and self._is_expanded:
            self._on_expand(self._issue["id"])

    def _on_hover(self, e: ft.HoverEvent) -> None:
        """Highlight row on hover."""
        self.bgcolor = ROW_HOVER if e.data else self._original_bgcolor
        self.update()
