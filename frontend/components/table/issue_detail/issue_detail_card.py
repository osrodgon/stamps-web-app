"""Issue detail card component — expanded issue details with stamps grid."""

from typing import Callable, Optional

import flet as ft

from components.colors import DARK_IMG_BG, GREY_700
from components.table.column_def import fmt_currency, fmt_date, fmt_number
from components.table.issue_detail.stamp_card import StampCard
from core.translations import _


class IssueDetailCard(ft.Container):
    """Expanded detail card showing full issue information and stamps.

    Displays three sections:
    - Identity Header: Series name, emission date, and inline valuation
      badges (Mint, Used, Total Printed).
    - Technical Specs: Responsive grid of issue attributes followed by
      description and notes text blocks.
    - Stamp Grid: Responsive grid of StampCard components.

    Args:
        issue: Raw issue data dict from the API response.
        stamps: List of stamp dicts wrapped in a dict with a "data" key.
        lang: Language code ("en" or "es").
        loading: If True, shows a loading placeholder in the stamp section.
        on_edit_stamp: Called with stamp ID when the edit icon is clicked.
        on_delete_stamp: Called with stamp ID when the delete icon is clicked.
    """

    def __init__(
        self,
        issue: dict,
        stamps: list[dict],
        lang: str,
        loading: bool = False,
        on_edit_stamp: Optional[Callable[[int], None]] = None,
        on_delete_stamp: Optional[Callable[[int], None]] = None,
        on_edit_issue: Optional[Callable[[int], None]] = None,
        on_delete_issue: Optional[Callable[[int], None]] = None,
        on_add_stamp: Optional[Callable[[int], None]] = None,
    ) -> None:
        super().__init__()
        self._issue: dict = issue
        self._stamps: list[dict] = stamps
        self._lang: str = lang
        self._loading: bool = loading
        self._on_edit_stamp: Optional[Callable[[int], None]] = on_edit_stamp
        self._on_delete_stamp: Optional[Callable[[int], None]] = on_delete_stamp
        self._on_edit_issue: Optional[Callable[[int], None]] = on_edit_issue
        self._on_delete_issue: Optional[Callable[[int], None]] = on_delete_issue
        self._on_add_stamp: Optional[Callable[[int], None]] = on_add_stamp

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
        issue_name: str = self._issue.get("name") or _("ui.no_text_value")
        date_str: str = fmt_date(self._issue.get("date", ""), self._lang)
        mint_value: float = float(self._issue.get("market_value_mnh") or 0)
        used_value: float = float(self._issue.get("market_value_used") or 0)
        total_printed: int = int(self._issue.get("total_printed") or 0)
        issue_actions_icon_size: int = 24

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(issue_name, size=32, font_family="Roboto-Black"),
                            ft.Row(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(_("stamps.mint"), size=14, font_family="Roboto-Black", color=GREY_700),
                                            ft.Container(content=ft.Text(fmt_currency(mint_value, self._lang), size=14, font_family="Roboto-Black", color=ft.Colors.GREEN_700), bgcolor=ft.Colors.GREEN_100, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=4)),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                    ft.Row(
                                        controls=[
                                            ft.Text(_("stamps.used"), size=14, font_family="Roboto-Black", color=GREY_700),
                                            ft.Container(content=ft.Text(fmt_currency(used_value, self._lang), size=14, font_family="Roboto-Black", color=ft.Colors.BLUE_700), bgcolor=ft.Colors.BLUE_100, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=4)),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                    ft.Row(
                                        controls=[
                                            ft.Text(_("stamps.total_printed"), size=14, font_family="Roboto-Black", color=GREY_700),
                                            ft.Container(content=ft.Text(fmt_number(total_printed, self._lang), size=14, font_family="Roboto-Black"), bgcolor=ft.Colors.GREY_300, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=4)),
                                        ],
                                        spacing=6,
                                    ),
                                ],
                                spacing=16,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_size=issue_actions_icon_size,
                                        splash_radius=1,
                                        splash_color=ft.Colors.TRANSPARENT,
                                        width=issue_actions_icon_size,
                                        height=issue_actions_icon_size,
                                        padding=0,
                                        hover_color=ft.Colors.TRANSPARENT,
                                        style=ft.ButtonStyle(
                                            color={
                                                ft.ControlState.DEFAULT: GREY_700,
                                                ft.ControlState.HOVERED: ft.Colors.ORANGE_700,
                                            },
                                            overlay_color=ft.Colors.TRANSPARENT,
                                        ),
                                        tooltip=_("issues.edit_tooltip"),
                                        on_click=self._handle_edit_issue,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_size=issue_actions_icon_size,
                                        splash_radius=1,
                                        splash_color=ft.Colors.TRANSPARENT,
                                        width=issue_actions_icon_size,
                                        height=issue_actions_icon_size,
                                        padding=0,
                                        hover_color=ft.Colors.TRANSPARENT,
                                        style=ft.ButtonStyle(
                                            color={
                                                ft.ControlState.DEFAULT: GREY_700,
                                                ft.ControlState.HOVERED: ft.Colors.RED_700,
                                            },
                                            overlay_color=ft.Colors.TRANSPARENT,
                                        ),
                                        on_click=self._handle_delete_issue,
                                        tooltip=_("issues.delete_tooltip")
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                                spacing=0,
                            )
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(date_str, size=16, color=GREY_700),
                ],
                spacing=4,
            ),
        )

    def _handle_edit_issue(self, e: ft.ControlEvent) -> None:
        issue_id = self._issue.get("id")
        if self._on_edit_issue and issue_id is not None:
            self._on_edit_issue(issue_id)

    def _handle_delete_issue(self, e: ft.ControlEvent) -> None:
        issue_id = self._issue.get("id")
        if self._on_delete_issue and issue_id is not None:
            self._on_delete_issue(issue_id)

    def _handle_add_stamp(self, e: ft.ControlEvent) -> None:
        issue_id = self._issue.get("id")
        if self._on_add_stamp and issue_id is not None:
            self._on_add_stamp(issue_id)

    def _build_specs(self) -> ft.Card:
        description: str = self._issue.get("description") or _("ui.no_text_value")
        notes: str = self._issue.get("note") or _("ui.no_text_value")

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
                    ],
                    spacing=12,
                ),
                padding=16,
            ),
        )

    def _detail_cell(self, icon: str, label: str, value: str, col: Optional[dict] = None) -> ft.Container:
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

        issue_year: str = str(self._issue.get("year", ""))

        stamp_controls: list[ft.Container] = [
            ft.Container(
                content=StampCard(
                    stamp=stamp,
                    issue_year=issue_year,
                    lang=self._lang,
                    on_edit=self._on_edit_stamp,
                    on_delete=self._on_delete_stamp,
                ),
                col={"sm": 6, "md": 3},
            )
            for stamp in sorted_stamps
        ]

        stamp_controls.append(
            ft.Container(
                content=ft.Card(
                    elevation=1,
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ADD, size=48, color=GREY_700),
                                    height=160,
                                    width=160,
                                    bgcolor=DARK_IMG_BG,
                                    border_radius=4,
                                    on_click=self._handle_add_stamp,
                                ),
                                ft.Text(
                                    _("stamps.add"),
                                    size=14,
                                    color=GREY_700,
                                    text_align=ft.TextAlign.CENTER,
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=12,
                    ),
                ),
                col={"sm": 6, "md": 3},
            )
        )

        return ft.ResponsiveRow(
            controls=stamp_controls,
            run_spacing=12,
        )
