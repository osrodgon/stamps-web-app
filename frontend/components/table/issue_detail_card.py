"""
Issue detail card component.

Expanded detail card displaying full issue information including
technical specifications, valuation summary, and nested stamp inventory.
"""

from typing import Optional

import flet as ft

from components.colors import GREY_700
from components.table.column_def import fmt_currency, fmt_date, fmt_number
from core.translations import _
from settings import NO_STAMP


class IssueDetailCard(ft.Container):
    """Expanded detail card showing full issue information and stamps.

    Displays 4 modules: Identity Header, Technical Specs Grid,
    Valuation Summary, and Stamp Inventory Table.

    Args:
        issue: Raw issue data dict from the API response.
        stamps: List of stamp dicts belonging to this issue.
        lang: Language code ("en" or "es").
        loading: If True, shows loading state in the stamp table.
    """

    def __init__(
        self,
        issue: dict,
        stamps: list[dict],
        lang: str,
        loading: bool = False,
    ) -> None:
        """Initialize the detail card with issue data and stamp list."""
        super().__init__()
        self._issue: dict = issue
        self._stamps: list[dict] = stamps
        self._lang: str = lang
        self._loading: bool = loading

        self.padding = 20
        self.bgcolor = ft.Colors.BLUE_GREY_50

        self.content = ft.Column(
            controls=[
                self._build_header(),
                self._build_specs(),
                self._build_stamp_table(),
            ],
            spacing=12,
        )

    def _build_header(self) -> ft.Container:
        """Module A: Identity & Header with series name and emission date."""
        issue_name: str = self._issue.get("name") or _("ui.no_text_value")
        date_str: str = fmt_date(self._issue.get("date", ""), self._lang)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        issue_name,
                        size=32,
                        font_family="Roboto-Black",
                    ),
                    ft.Text(
                        date_str,
                        size=16,
                        color=GREY_700,
                    ),
                ],
                spacing=4,
            ),
        )

    def _build_specs(self) -> ft.Card:
        """Unified issue details card with specs, description, notes, and valuation."""
        description: str = self._issue.get("description") or _("ui.no_text_value")
        notes: str = self._issue.get("note") or _("ui.no_text_value")
        mint_value: float = float(self._issue.get("market_value_mnh") or 0)
        used_value: float = float(self._issue.get("market_value_used") or 0)
        total_printed: int = int(self._issue.get("total_printed") or 0)

        return ft.Card(
            elevation=1,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ResponsiveRow(
                            controls=[
                                self._detail_cell(ft.Icons.FLAG, _("stamps.country"), self._issue.get("country") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.CATEGORY, _("stamps.stamp_type"), self._issue.get("stamp_type") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.FACTORY, _("stamps.printer"), self._issue.get("printer") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.CALENDAR_TODAY, _("stamps.year"), self._issue.get("year") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.GRID_ON, _("stamps.perforation"), self._issue.get("perforation") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.PRINT, _("stamps.print_type"), self._issue.get("print_type") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.BRUSH, _("stamps.artist"), self._issue.get("artist") or "-", col={"sm": 6, "md": 4}),
                                self._detail_cell(ft.Icons.DESCRIPTION, _("stamps.paper_type"), self._issue.get("paper_type") or "-", col={"sm": 6, "md": 4}),
                            ],
                            run_spacing=8,
                        ),
                        ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    _("ui.description").upper(),
                                    size=14,
                                    font_family="Roboto-Black",
                                    color=GREY_700,
                                ),
                                ft.Text(
                                    str(description),
                                    size=14,
                                    font_family="Roboto",
                                    text_align=ft.TextAlign.JUSTIFY,
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    _("ui.notes").upper(),
                                    size=14,
                                    font_family="Roboto-Black",
                                    color=GREY_700,
                                ),
                                ft.Text(
                                    str(notes),
                                    size=14,
                                    font_family="Roboto",
                                    text_align=ft.TextAlign.JUSTIFY,
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            _("stamps.market_value_mnh") or _("stamps.mint"),
                                            size=14,
                                            font_family="Roboto-Black",
                                            color=GREY_700,
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                fmt_currency(mint_value, self._lang),
                                                size=16,
                                                font_family="Roboto-Black",
                                                color=ft.Colors.GREEN_700,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ft.Colors.GREEN_100,
                                            border_radius=8,
                                            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                                        ),
                                    ],
                                    spacing=2,
                                ),
                                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            _("stamps.market_value_used") or _("stamps.used"),
                                            size=14,
                                            font_family="Roboto-Black",
                                            color=GREY_700,
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                fmt_currency(used_value, self._lang),
                                                size=16,
                                                font_family="Roboto-Black",
                                                color=ft.Colors.BLUE_700,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ft.Colors.BLUE_100,
                                            border_radius=8,
                                            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                                        ),
                                    ],
                                    spacing=2,
                                ),
                                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            _("stamps.total_printed"),
                                            size=14,
                                            font_family="Roboto-Black",
                                            color=GREY_700,
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                fmt_number(total_printed, self._lang),
                                                size=16,
                                                font_family="Roboto-Black",
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ft.Colors.GREY_300,
                                            border_radius=8,
                                            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                    spacing=12,
                ),
                padding=16,
            ),
        )

    def _detail_cell(self, icon: str, label: str, value: str, col: Optional[dict] = None) -> ft.Container:
        """Create a single detail cell with icon, label, and value."""
        container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Icon(icon, size=18, color=GREY_700), width=18),
                    ft.Column(
                        controls=[
                            ft.Text(
                                label.upper(),
                                size=14,
                                font_family="Roboto-Black",
                                color=GREY_700,
                            ),
                            ft.Text(
                                value,
                                size=14,
                                font_family="Roboto",
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        if col:
            container.col = col
        return container

    def _build_stamp_table(self) -> ft.Control:
        """Module D: Stamp Catalog - custom card list with descriptions."""
        if self._loading:
            return ft.Container(
                content=ft.Text(
                    _("stamps.loading_stamps"),
                    size=14,
                    color=GREY_700,
                ),
                padding=10,
            )

        if not self._stamps:
            return ft.Container(
                content=ft.Text(
                    _("stamps.no_stamps_found"),
                    size=14,
                    color=GREY_700,
                ),
                padding=10,
            )

        sorted_stamps: list[dict] = sorted(
            self._stamps.get("data", []),
            key=lambda s: s.get("fesofi_code") or "",
        )

        return ft.Column(
            controls=[self._build_stamp_card(stamp) for stamp in sorted_stamps],
            spacing=8,
        )

    def _build_stamp_card(self, stamp: dict) -> ft.Card:
        """Build a single stamp card with 200x200 image, info, and description."""
        colors_list: list[str] = stamp.get("colors", [])
        colors_str: str = ", ".join(colors_list) if colors_list else "-"
        image_url: Optional[str] = stamp.get("image")

        stamp_mnh: float = float(stamp.get("market_value_mnh") or 0)
        stamp_used: float = float(stamp.get("market_value_used") or 0)
        stamp_total: int = int(stamp.get("total_printed") or 0)
        description: str = stamp.get("description") or _("ui.no_text_value")

        codes_text: str = f"{_('stamps.edifil_code')}: {stamp.get('edifil_code') or '-'}  |  {_('stamps.fesofi_code')}: {stamp.get('fesofi_code') or '-'}"
        details_text: str = f"{_('stamps.face_value')}: {stamp.get('face_value') or '-'}  |  {_('stamps.color')}: {colors_str}"
        mnh_part: str = f"{_('stamps.mint')}: {fmt_currency(stamp_mnh, self._lang)}"
        used_part: str = f"{_('stamps.used')}: {fmt_currency(stamp_used, self._lang)}"
        tp_part: str = f"{_('stamps.total_printed')}: {fmt_number(stamp_total, self._lang)}"

        return ft.Card(
            elevation=1,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Image(
                                        src=image_url,
                                        fit="contain",
                                        width=180,
                                        height=180,
                                    ) if image_url else ft.Image(
                                        src=NO_STAMP,
                                        fit="contain",
                                        width=180,
                                        height=180,
                                    ),
                                    width=180,
                                    height=180,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(stamp.get("name") or "-", size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(codes_text, size=14, color=GREY_700),
                                        ft.Text(details_text, size=14, color=GREY_700),
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Text(mnh_part, size=14, color=GREY_700),
                                                    bgcolor=ft.Colors.GREEN_100,
                                                    border_radius=6,
                                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                ),
                                                ft.Container(
                                                    content=ft.Text(used_part, size=14, color=GREY_700),
                                                    bgcolor=ft.Colors.BLUE_100,
                                                    border_radius=6,
                                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                ),
                                                ft.Container(
                                                    content=ft.Text(tp_part, size=14, color=GREY_700),
                                                    bgcolor=ft.Colors.GREY_300,
                                                    border_radius=6,
                                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                ),
                                            ],
                                            spacing=4,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            wrap=True,
                                        ),
                                        ft.Text(
                                            description,
                                            size=14,
                                            text_align=ft.TextAlign.JUSTIFY,
                                            margin=ft.Margin(top=10),
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ],
                    spacing=4,
                ),
                padding=12,
                expand=True,
            ),
            expand=True,
        )