"""A collection card: collage, name, counters and progress (plan step A4).

The card is what the overview screen repeats: up to six stamps of the collection as
its cover, the name, how many series and stamps it holds, and a bar that says how
much of those series is already in it.

The pictures are files on the frontend (`assets/stamps/<year>/<code>.webp`), so the
component is the one that decides which of the covers the API sent can be painted —
that is why the API sends twelve for a collage of six.
"""

from __future__ import annotations

import os
from typing import Callable, List, Optional, Tuple

import flet as ft

from components.colors import BG_ALT, GREY_700, ROW_BORDER, SKY_BLUE
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_PADDING,
    CARD_SHADOW_BLUR,
    CARD_SHADOW_OPACITY,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XS,
)
from components.table.column_def import fmt_number
from core.translations import _
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP


class CollectionCard(ft.Container):
    """One collection of the overview, as a card.

    Args:
        data: the overview row (`id`, `name`, `series`, `stamps`, `total`, `covers`).
        lang: the active language, for the numbers.
        on_open: reserved for the series screen; not used until B3, because the
            route does not exist yet and a card that looks clickable and does
            nothing is worse than one that does not.
        on_rename: when given, the card shows a menu with "Rename".
        on_delete: when given, the menu also offers "Delete".
    """

    #: The collage never paints more than this, however many covers the API sends.
    MAX_COVERS: int = 6
    #: The mosaic uses three columns, so six stamps fill two rows with no holes.
    COLUMNS: int = 3
    COVER_HEIGHT: int = 168
    COVER_PADDING: int = 14
    THUMBNAIL_HEIGHT: int = 56
    SINGLE_THUMBNAIL_HEIGHT: int = 124
    PROGRESS_HEIGHT: int = 6
    THUMBNAIL_SPACING: int = 6

    def __init__(
        self,
        data: dict,
        lang: str,
        on_open: Optional[Callable[[int], None]] = None,
        on_rename: Optional[Callable[[dict], None]] = None,
        on_delete: Optional[Callable[[dict], None]] = None,
    ) -> None:
        super().__init__()
        self._data: dict = data
        self._lang: str = lang
        self._on_open: Optional[Callable[[int], None]] = on_open
        self._on_rename: Optional[Callable[[dict], None]] = on_rename
        self._on_delete: Optional[Callable[[dict], None]] = on_delete

        # Exposed to the tests and to B3: what the card painted and what it says.
        self._images: List[ft.Image] = []
        self._summary: ft.Text = ft.Text("")
        self._percentage: ft.Text = ft.Text("")
        self._progress: ft.ProgressBar = ft.ProgressBar()
        self._menu: Optional[ft.PopupMenuButton] = self._actions()

        self.content = ft.Column(
            controls=[self._cover(), self._body()],
            spacing=0,
            tight=True,
        )
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border.all(1, ROW_BORDER)
        self.border_radius = CARD_BORDER_RADIUS
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.shadow = ft.BoxShadow(
            blur_radius=CARD_SHADOW_BLUR,
            color=ft.Colors.with_opacity(CARD_SHADOW_OPACITY, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        )

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------

    def _cover(self) -> ft.Container:
        """The collage: six stamps, one big, or the placeholder."""
        sources = self._existing_covers()

        if not sources:
            collage: ft.Control = self._image(
                NO_STAMP, self.SINGLE_THUMBNAIL_HEIGHT, faded=True
            )
        elif len(sources) == 1:
            year, code = sources[0]
            collage = self._image(
                self._source(year, code), self.SINGLE_THUMBNAIL_HEIGHT
            )
        else:
            rows = []
            for start in range(0, len(sources), self.COLUMNS):
                rows.append(
                    ft.Row(
                        controls=[
                            self._image(self._source(year, code), self.THUMBNAIL_HEIGHT)
                            for year, code in sources[start:start + self.COLUMNS]
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=self.THUMBNAIL_SPACING,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )
            collage = ft.Column(
                controls=rows,
                spacing=self.THUMBNAIL_SPACING,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        return ft.Container(
            content=collage,
            height=self.COVER_HEIGHT,
            padding=self.COVER_PADDING,
            bgcolor=BG_ALT,
            border=ft.Border(bottom=ft.BorderSide(1, ROW_BORDER)),
            alignment=ft.Alignment.CENTER,
        )

    def _existing_covers(self) -> List[Tuple[str, str]]:
        """The first covers whose picture file exists, up to `MAX_COVERS`."""
        found: List[Tuple[str, str]] = []
        for cover in self._data.get("covers") or []:
            year = cover.get("year")
            code = cover.get("code")
            if year is None or not code:
                continue
            if os.path.exists(os.path.join(IMAGE_DIR, str(year), f"{code}.webp")):
                found.append((str(year), str(code)))
            if len(found) == self.MAX_COVERS:
                break
        return found

    def _image(self, src: str, height: int, faded: bool = False) -> ft.Image:
        """One picture of the collage, remembered for the tests."""
        # Square cells: the mosaic lines up whatever the stamp's aspect ratio,
        # and `fit=CONTAIN` keeps the piece itself undistorted. The admin's cards
        # also set both sides.
        image = ft.Image(
            src=src,
            width=height,
            height=height,
            fit=ft.BoxFit.CONTAIN,
            opacity=0.55 if faded else 1,
        )
        self._images.append(image)
        return image

    @staticmethod
    def _source(year: str, code: str) -> str:
        """The Flet source of a cover, relative to the assets folder."""
        return os.path.join(
            os.path.relpath(IMAGE_DIR, ASSETS_DIR), year, f"{code}.webp"
        )

    # ------------------------------------------------------------------
    # Body
    # ------------------------------------------------------------------

    def _body(self) -> ft.Container:
        """The name, the summary and the progress line."""
        series = int(self._data.get("series") or 0)
        stamps = int(self._data.get("stamps") or 0)
        total = int(self._data.get("total") or 0)

        self._summary = ft.Text(
            _(
                "collections.summary",
                series=fmt_number(series, self._lang, zero="0"),
                stamps=fmt_number(stamps, self._lang, zero="0"),
            ),
            size=FONT_SIZE_XS,
            color=GREY_700,
        )
        self._percentage = ft.Text(
            self._percentage_text(stamps, total),
            size=FONT_SIZE_XS,
            weight=ft.FontWeight.BOLD,
        )
        self._progress = ft.ProgressBar(
            value=(stamps / total) if total else 0,
            color=SKY_BLUE,
            bgcolor=BG_ALT,
            bar_height=self.PROGRESS_HEIGHT,
            border_radius=self.PROGRESS_HEIGHT // 2,
            expand=True,
        )

        name = ft.Text(
            self._data.get("name") or "",
            size=FONT_SIZE_SMALL_HEADING,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        title = (
            ft.Row(
                controls=[name, self._menu],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            if self._menu is not None
            else name
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    title,
                    self._summary,
                    ft.Row(
                        controls=[self._progress, self._percentage],
                        spacing=self.THUMBNAIL_SPACING,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=self.THUMBNAIL_SPACING,
                tight=True,
            ),
            padding=CARD_PADDING,
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _actions(self) -> Optional[ft.PopupMenuButton]:
        """The card's menu, when the page gives it something to do."""
        items: List[ft.PopupMenuItem] = []
        if self._on_rename is not None:
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(_("collections.rename")),
                    icon=ft.Icons.EDIT,
                    on_click=lambda event: self._on_rename(self._data),
                )
            )
        if self._on_delete is not None:
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(_("collections.delete_title")),
                    icon=ft.Icons.DELETE_OUTLINE,
                    on_click=lambda event: self._on_delete(self._data),
                )
            )
        if not items:
            return None
        return ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, items=items)

    @staticmethod
    def _percentage_text(stamps: int, total: int) -> str:
        """`64%`, or `—` when there is nothing to complete."""
        if not total:
            return "—"
        return f"{round(stamps * 100 / total)}%"
