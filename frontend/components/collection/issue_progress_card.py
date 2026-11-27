"""One series of a collection, as a row of the second screen (plan step B3).

The row is what `/collections/<id>` repeats: the cover, when the series is, how much of
it the user owns and what it cost, next to what the catalogue says it is worth.

It is a link when the page gives it `on_open`: a row that looks clickable and does
nothing is worse than one that does not.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

import flet as ft

from components.colors import (
    BG_ALT,
    DARK_BLUE_GREY,
    GREY_700,
    ICON_GREY,
    ROW_BORDER,
    SKY_BLUE,
)
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_SHADOW_BLUR,
    CARD_SHADOW_OPACITY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XS,
    STANDARD_PADDING,
)
from components.table.column_def import fmt_currency, fmt_date, fmt_number
from core.translations import _
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP


class IssueProgressCard(ft.Container):
    """A series with its cover, its progress and its two figures.

    Args:
        data: one row of the series endpoint (`year`, `date`, `name`, `country`,
            `stamp_type`, `cover`, `total_stamps`, `owned_stamps`, `paid`,
            `catalogue_mnh`).
        lang: the active language, for the numbers and the date.
        on_open: called with the series' id when the row is clicked; when it is
            None the row is not clickable.
    """

    THUMBNAIL_SIZE: int = 64
    THUMBNAIL_PADDING: int = 4
    BAR_HEIGHT: int = 6
    FIGURES_SPACING: int = 24
    CHEVRON_SIZE: int = 20

    def __init__(
        self,
        data: dict,
        lang: str,
        on_open: Optional[Callable[[int], None]] = None,
    ) -> None:
        super().__init__()
        self._data: dict = data
        self._lang: str = lang
        self._on_open: Optional[Callable[[int], None]] = on_open

        # Exposed to the tests: what the row painted and what it says.
        self._image: ft.Image = self.__image()
        self._progress_bar: ft.ProgressBar = self.__progress_bar()
        self._progress_text: ft.Text = self.__progress_text()
        self._percentage: ft.Text = self.__percentage()

        self.content = ft.Row(
            controls=[
                self.__thumbnail(),
                self.__identity(),
                self.__progress(),
                self.__figures(),
                ft.Icon(
                    ft.Icons.CHEVRON_RIGHT,
                    size=self.CHEVRON_SIZE,
                    color=ICON_GREY,
                ),
            ],
            spacing=STANDARD_PADDING,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.padding = ft.Padding.symmetric(
            horizontal=STANDARD_PADDING, vertical=STANDARD_PADDING
        )
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border.all(1, ROW_BORDER)
        self.border_radius = CARD_BORDER_RADIUS
        self.shadow = ft.BoxShadow(
            blur_radius=CARD_SHADOW_BLUR,
            color=ft.Colors.with_opacity(CARD_SHADOW_OPACITY, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        )
        if on_open is not None:
            self.on_click = self._handle_open

    def _handle_open(self, event: ft.ControlEvent) -> None:
        """Open the series."""
        if self._on_open is not None:
            self._on_open(int(self._data.get("id") or 0))

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------

    def __image(self) -> ft.Image:
        """The picture of the cover, or the placeholder."""
        cover = self._data.get("cover") or {}
        year = cover.get("year")
        code = cover.get("code")
        source = NO_STAMP
        faded = True

        if year is not None and code:
            path = os.path.join(IMAGE_DIR, str(year), f"{code}.webp")
            if os.path.exists(path):
                source = os.path.join(
                    os.path.relpath(IMAGE_DIR, ASSETS_DIR), str(year), f"{code}.webp"
                )
                faded = False

        return ft.Image(
            src=source,
            width=self.THUMBNAIL_SIZE - 2 * self.THUMBNAIL_PADDING,
            height=self.THUMBNAIL_SIZE - 2 * self.THUMBNAIL_PADDING,
            fit=ft.BoxFit.CONTAIN,
            opacity=0.55 if faded else 1,
        )

    def __thumbnail(self) -> ft.Container:
        """The plate behind the picture."""
        return ft.Container(
            width=self.THUMBNAIL_SIZE,
            height=self.THUMBNAIL_SIZE,
            padding=self.THUMBNAIL_PADDING,
            bgcolor=BG_ALT,
            border_radius=CARD_BORDER_RADIUS,
            alignment=ft.Alignment.CENTER,
            content=self._image,
        )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def __identity(self) -> ft.Container:
        """When the series is and what it is called."""
        year = self._data.get("year") or ""
        issued = fmt_date(self._data.get("date") or "", self._lang)
        country = self._data.get("country") or "-"
        stamp_type = self._data.get("stamp_type") or "-"

        return ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"{year} · {issued}",
                        size=FONT_SIZE_XS,
                        color=GREY_700,
                    ),
                    ft.Text(
                        self._data.get("name") or "",
                        size=FONT_SIZE_SMALL_HEADING,
                        weight=ft.FontWeight.BOLD,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"{country} · {stamp_type}",
                        size=FONT_SIZE_XS,
                        color=GREY_700,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=2,
                tight=True,
            ),
        )

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def __owned(self) -> int:
        """How many stamps of the series the user owns."""
        return int(self._data.get("owned_stamps") or 0)

    def __total(self) -> int:
        """How many stamps the series has."""
        return int(self._data.get("total_stamps") or 0)

    def __progress_text(self) -> ft.Text:
        """`3 of 5 stamps`, from the locale key."""
        return ft.Text(
            _(
                "collections.progress",
                owned=fmt_number(self.__owned(), self._lang, zero="0"),
                total=fmt_number(self.__total(), self._lang, zero="0"),
            ),
            size=FONT_SIZE_XS,
            color=GREY_700,
        )

    def __percentage(self) -> ft.Text:
        """`60%`, or `—` when the series has no stamps."""
        total = self.__total()
        text = f"{round(self.__owned() * 100 / total)}%" if total else "—"
        return ft.Text(
            text, size=FONT_SIZE_XS, weight=ft.FontWeight.BOLD
        )

    def __progress_bar(self) -> ft.ProgressBar:
        """The bar, proportional to the owned stamps."""
        total = self.__total()
        return ft.ProgressBar(
            value=(self.__owned() / total) if total else 0,
            color=SKY_BLUE,
            bgcolor=BG_ALT,
            bar_height=self.BAR_HEIGHT,
            border_radius=self.BAR_HEIGHT // 2,
            expand=True,
        )

    def __progress(self) -> ft.Container:
        """`3 of 5 stamps` and its percentage, with the bar underneath.

        As the mockup: the two texts share a line and the bar takes the width, so a
        series at 0% and one at 100% paint the same bar.
        """
        return ft.Container(
            width=220,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._progress_text,
                            ft.Container(expand=True),
                            self._percentage,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._progress_bar,
                ],
                spacing=6,
                tight=True,
            ),
        )

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------

    def __figure(self, label: str, value) -> ft.Column:
        """One label above its amount."""
        return ft.Column(
            controls=[
                ft.Text(
                    label,
                    size=FONT_SIZE_XS,
                    color=GREY_700,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Text(
                    fmt_currency(value, self._lang),
                    size=FONT_SIZE_DEFAULT,
                    weight=ft.FontWeight.BOLD,
                    color=DARK_BLUE_GREY,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.END,
        )

    def __figures(self) -> ft.Row:
        """What the user paid and what the catalogue says the series is worth."""
        return ft.Row(
            controls=[
                self.__figure(_("collections.paid"), self._data.get("paid")),
                self.__figure(
                    _("collections.catalogue"), self._data.get("catalogue_mnh")
                ),
            ],
            spacing=self.FIGURES_SPACING,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
