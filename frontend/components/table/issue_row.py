"""
Issue row component for the issue table.

Provides a single row displaying stamp issue data with expandable details.
"""

from typing import Callable, Optional

import flet as ft

from components.colors import (
    BG_ALT,
    BG_LIGHT,
    DARK_BLUE_GREY,
    EXPANSION_BG,
    ROW_BORDER,
    ROW_HOVER,
    TEXT_BLUE,
)
from components.table.column_def import ColumnDef
from components.table.issue_detail_card import IssueDetailCard
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
        expanded: bool = False,
    ) -> None:
        """Initialize a single issue row with data cells and expandable details.

        Builds the row layout from the COLUMNS definition, applies zebra
        striping based on row_index, and wires the hover and expand events.

        Args:
            issue: Raw issue data dict from the API response.
            row_index: Zero-based index for zebra striping.
            columns: List of ColumnDef to build cells from.
            lang: Language code for locale-aware formatting ("en" or "es").
            on_expand: Called with issue ID when the chevron is toggled open.
            expanded: If True, start with details expanded (used for first row on page 1).
        """
        super().__init__()
        self._issue: dict = issue
        self._row_index: int = row_index
        self._columns: list[ColumnDef] = columns or []
        self._lang: str = lang
        self._on_expand: Optional[Callable[[int], None]] = on_expand
        self._is_expanded: bool = expanded
        self._original_bgcolor: str | None = BG_LIGHT if row_index % 2 == 0 else BG_ALT
        self._stamps: list[dict] = []
        self._loading_stamps: bool = False

        self._chevron_icon: ft.Icon = ft.Icon(
            icon=ft.Icons.KEYBOARD_ARROW_UP if expanded else ft.Icons.KEYBOARD_ARROW_DOWN,
            size=16,
            color=ft.Colors.WHITE,
        )
        self._details: ft.Container = ft.Container(
            content=self._build_details() if expanded else None,
            visible=expanded,
        )

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

        return ft.Container(
            content=ft.Row(
                controls=cells,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=14, right=25, top=12, bottom=12),
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
            **kwargs,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _build_details(self) -> IssueDetailCard:
        """Build the expanded detail card with full issue and stamp info."""
        return IssueDetailCard(
            issue=self._issue,
            stamps=self._stamps,
            lang=self._lang,
            loading=self._loading_stamps,
        )

    def set_loading(self) -> None:
        """Set the details card to loading state.

        Used when the row is auto-expanded (e.g. rows_per_page=1)
        to show a loading indicator while stamps are fetched asynchronously.
        Does not call update() — parent is responsible for that.
        """
        if not self._is_expanded:
            return
        self._loading_stamps = True
        self._details.content = self._build_details()

    def set_stamps(self, stamps: list[dict]) -> None:
        """Update stamps data and rebuild the details card.

        Called by the parent IssueTableApp after async stamp fetch.

        Args:
            stamps: List of stamp dicts from the API.
        """
        self._stamps = stamps
        self._loading_stamps = False
        if self._is_expanded:
            self._details.content = self._build_details()
            self.update()

    def _toggle_expand(self, e: ft.ControlEvent) -> None:
        """Toggle the details section visibility."""
        self._is_expanded = not self._is_expanded

        self._chevron_icon.icon = (
            ft.Icons.KEYBOARD_ARROW_UP
            if self._is_expanded
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )

        if self._is_expanded:
            self._loading_stamps = self._stamps == []
            self._details.content = self._build_details()
        self._details.visible = self._is_expanded
        self.update()

        issue_id = self._issue.get("id")
        if self._on_expand and self._is_expanded and issue_id is not None:
            self._on_expand(issue_id)

    def _on_hover(self, e: ft.HoverEvent) -> None:
        """Highlight row on hover."""
        self.bgcolor = ROW_HOVER if e.data else self._original_bgcolor
        self.update()
