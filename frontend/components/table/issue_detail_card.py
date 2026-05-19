"""
Issue detail card component.

Expanded detail card displayed when an issue row is expanded in the
IssueTable. Shows the issue identity header with inline valuation badges,
a technical specifications grid with description and notes, and a responsive
grid of stamp cards with image thumbnails, catalog codes, and a tooltip
indicator for stamps that have additional description text.
"""

import os
from math import exp
from pydoc import text
from typing import Optional

import flet as ft
from PIL import Image as PILImage

from components.colors import DARK_IMG_BG, GREY_700
from components.table.column_def import fmt_currency, fmt_date, fmt_number
from core.translations import _
from components.buttons.default_button import DefaultButton
from settings import ASSETS_DIR, NO_STAMP, IMAGE_DIR


class IssueDetailCard(ft.Container):
    """Expanded detail card showing full issue information and stamps.

    Displays three sections:
    - Identity Header: Series name, emission date, and inline valuation
      badges (Mint, Used, Total Printed).
    - Technical Specs: Responsive grid of issue attributes (country, type,
      printer, year, perforation, print type, artist, paper type) followed
      by description and notes text blocks.
    - Stamp Grid: Responsive card layout (2 columns on small screens, 3 on
      medium+) showing stamp thumbnails, catalog codes, face value, colors,
      and market values. Stamps with description text show an indicator icon
      with a hover tooltip.

    Args:
        issue: Raw issue data dict from the API response.
        stamps: List of stamp dicts belonging to this issue, wrapped in a
            dict with a "data" key (API response format).
        lang: Language code ("en" or "es").
        loading: If True, shows a loading placeholder in the stamp section.
    """

    def __init__(
        self,
        issue: dict,
        stamps: list[dict],
        lang: str,
        loading: bool = False,
    ) -> None:
        """Initialize the detail card with issue data and stamp list.

        Stores the issue and stamp data, configures the card padding and
        background color, and builds the three-section layout: header,
        specs, and stamp grid.

        Args:
            issue: Raw issue data dict from the API response.
            stamps: Stamp data dict containing a "data" key with the list
                of stamp dicts, or an empty list if no stamps.
            lang: Language code for locale-aware formatting ("en" or "es").
            loading: If True, shows a loading placeholder instead of the
                stamp grid.
        """
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
        """Build the identity header with series name, date, and valuation badges.

        Displays the issue name in large bold text, the emission date below
        it, and three inline valuation badges (Mint/MNH, Used, Total Printed)
        aligned to the right of the series name.

        Returns:
            Container with the header layout.
        """
        issue_name: str = self._issue.get("name") or _("ui.no_text_value")
        date_str: str = fmt_date(self._issue.get("date", ""), self._lang)
        mint_value: float = float(self._issue.get("market_value_mnh") or 0)
        used_value: float = float(self._issue.get("market_value_used") or 0)
        total_printed: int = int(self._issue.get("total_printed") or 0)

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
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(date_str, size=16, color=GREY_700),
                ],
                spacing=4,
            ),
        )

    def _build_specs(self) -> ft.Card:
        """Build the technical specifications card with description and notes.

        Creates a responsive grid of attribute cells (country, stamp type,
        printer, year, perforation, print type, artist, paper type) followed
        by the issue description and notes text blocks.

        Returns:
            Card containing the specs grid and narrative text sections.
        """
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
        """Create a single specification cell with an icon, label, and value.

        Each cell displays a small icon on the left, with the label text
        (uppercase) and value text stacked vertically on the right.

        Args:
            icon: Flet icon name (e.g., ft.Icons.FLAG).
            label: Display label for the attribute.
            value: The attribute value to display.
            col: Optional responsive column span dict (e.g., {"sm": 6, "md": 4}).

        Returns:
            Container configured as a responsive grid cell.
        """
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

    def _get_native_image_height(self, image_path: str) -> int:
        """Get the native height of an image, capped at 450px.

        Args:
            image_path: Path relative to ASSETS_DIR, or NO_STAMP filename.

        Returns:
            Native image height if under 450, else 450.
        """
        abs_path: str = os.path.join(ASSETS_DIR, NO_STAMP) if image_path == NO_STAMP else os.path.join(ASSETS_DIR, image_path)
        try:
            with PILImage.open(abs_path) as img:
                return min(img.height, 450)
        except Exception:
            return 450

    def _show_stamp_detail(self, image_path: str, description: str) -> None:
        """Open a dialog showing the full-size stamp image and description.

        Args:
            image_path: Path to the stamp image (relative to assets_dir).
            description: The stamp's description text.
        """
        page = self.page
        if not page:
            return

        display_height: int = self._get_native_image_height(image_path)

        def close(_: ft.ControlEvent | None = None) -> None:
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Image(src=image_path, fit="contain", height=display_height),
                                    bgcolor=DARK_IMG_BG,
                            border_radius=4,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text(description, size=15, font_family="Roboto", text_align=ft.TextAlign.JUSTIFY),
                            visible=bool(description),
                        ),
                    ],
                    spacing=16,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=600,
            ),
            actions=[DefaultButton(_("ui.close"), on_click=close)],
            on_dismiss=close,
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _build_stamp_table(self) -> ft.Control:
        """Build the stamp inventory section as a responsive card grid.

        Handles three states: loading (shows placeholder), empty (shows
        "no stamps" message), and populated (renders a ResponsiveRow of
        stamp cards sorted by FESOFI code). Cards are displayed 2 per row
        on small screens and 3 per row on medium screens.

        Returns:
            Container for loading/empty states, or ResponsiveRow of stamp cards.
        """
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

        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=self._build_stamp_card(stamp),
                    col={"sm": 6, "md": 4},
                )
                for stamp in sorted_stamps
            ],
            run_spacing=12,
        )

    def _build_stamp_card(self, stamp: dict) -> ft.Card:
        """Build a single stamp card with thumbnail, catalog info, and valuations.

        Each card displays a stamp image (or fallback placeholder),
        the stamp name (with ellipsis overflow), FESOFI and Edifil catalog
        codes, face value, colors, and MNH/Used market value badges. If the
        stamp has a description, an indicator icon with a click-to-open
        dialog showing the full-size image and description.

        Args:
            stamp: Stamp data dict from the API response.

        Returns:
            Card widget containing the stamp information.
        """
        colors_list: list[str] = stamp.get("colors", [])
        colors_str: str = ", ".join(colors_list) if colors_list else "-"

        year: str = str(self._issue.get("year", ""))
        fesofi_code: str = stamp.get("fesofi_code") or ""
        image_rel: str = os.path.join(os.path.relpath(IMAGE_DIR, ASSETS_DIR), year, f"{fesofi_code}.webp")
        image_path: str = image_rel if os.path.exists(os.path.join(IMAGE_DIR, year, f"{fesofi_code}.webp")) else NO_STAMP

        stamp_mnh: float = float(stamp.get("market_value_mnh") or 0)
        stamp_used: float = float(stamp.get("market_value_used") or 0)

        description: str = stamp.get("description") or ""

        codes_text: str = f"FESOFI: {stamp.get('fesofi_code') or '-'}  |  Edifil: {stamp.get('edifil_code') or '-'}"
        face_value_text: str = f"{_('stamps.face_value')}: {stamp.get('face_value') or '-'}"
        color_text: str = f"{_("stamps.color")}: {colors_str}"
        mnh_part: str = f"{_('stamps.mint')}: {fmt_currency(stamp_mnh, self._lang)}"
        used_part: str = f"{_('stamps.used')}: {fmt_currency(stamp_used, self._lang)}"

        return ft.Card(
            elevation=1,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Image(
                                        src=image_path,
                                        fit="contain",
                                        height=160,
                                    ),
                                    height=160,
                            bgcolor=DARK_IMG_BG,
                                    border_radius=4,
                                    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK_26, offset=ft.Offset(1, 2)),
                                    on_click=lambda e, p=image_path, d=description: self._show_stamp_detail(p, d),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(stamp.get("name") or "-", size=15, weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(codes_text, size=14, color=GREY_700),
                                        ft.Text(face_value_text, size=14, color=GREY_700),
                                        ft.Text(color_text, size=14, color=GREY_700),
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
                                    ] + (
                                        [
                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.ARTICLE, size=16, color=GREY_700),
                                                        ft.Text(_("ui.description").upper(), font_family="Roboto-Black", size=12, color=GREY_700),
                                                    ],
                                                    spacing=4,
                                                ),
                                                on_click=lambda e, p=image_path, d=description: self._show_stamp_detail(p, d),
                                            )
                                        ]
                                        if description
                                        else []
                                    ),
                                    spacing=6,
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