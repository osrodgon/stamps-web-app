"""Stamp inventory grid — loading, empty, or sorted StampCards."""

from typing import Any, Callable, Optional

import flet as ft

from components.colors import GREY_700
from components.table.issue_detail.stamp_card import StampCard
from core.translations import _
from components.constants import (
    CARD_ELEVATION,
    FONT_SIZE_DEFAULT,
    STAMP_ADD_ICON_SIZE,
    STANDARD_PADDING,
)

_ADD_STAMP_CARD_HEIGHT: int = 184


class IssueStampGrid(ft.Container):
    """Stamp inventory grid with loading, empty, and populated states.

    Renders sorted StampCards in a responsive grid with an add-stamp
    button as the last item. Delegates to ``StampCard`` for individual
    stamp display.

    Args:
        stamps: Dict with a ``"data"`` key containing a list of stamp dicts.
        loading: If True, shows a loading placeholder.
        lang: Language code (``"en"`` or ``"es"``).
        issue_year: Year string for stamp display context.
        on_edit_stamp: Called with stamp ID when the edit icon is clicked.
        on_delete_stamp: Called with stamp ID (issue ID already baked in).
        on_add_stamp: Called with event (issue ID baked in by coordinator).
    """

    def __init__(
        self,
        stamps: dict,
        loading: bool,
        lang: str,
        issue_year: str,
        on_edit_stamp: Optional[Callable[[dict], Any]] = None,
        on_delete_stamp: Optional[Callable[[int], Any]] = None,
        on_add_stamp: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._stamps: dict = stamps
        self._loading: bool = loading
        self._lang: str = lang
        self._issue_year: str = issue_year
        self._on_edit_stamp: Optional[Callable[[dict], Any]] = on_edit_stamp
        self._on_delete_stamp: Optional[Callable[[int], Any]] = on_delete_stamp
        self._on_add_stamp: Optional[Callable] = on_add_stamp

        self.content = self._build_stamp_content()

    def _build_stamp_content(self) -> ft.Control:
        if self._loading:
            return ft.Container(
                content=ft.Text(
                    _("stamps.loading_stamps"),
                    size=14,
                    color=GREY_700,
                ),
                padding=STANDARD_PADDING,
            )

        if not self._stamps:
            return ft.Container(
                content=ft.Text(
                    _("stamps.no_stamps_found"),
                    size=FONT_SIZE_DEFAULT,
                    color=GREY_700,
                ),
                padding=STANDARD_PADDING,
            )

        sorted_stamps = sorted(
            self._stamps.get("data", []),
            key=lambda s: s.get("fesofi_code") or "",
        )

        stamp_controls = [
            ft.Container(
                content=StampCard(
                    stamp=stamp,
                    issue_year=self._issue_year,
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
                    elevation=CARD_ELEVATION,
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        icon_size=STAMP_ADD_ICON_SIZE,
                                        splash_radius=1,
                                        splash_color=ft.Colors.TRANSPARENT,
                                        width=STAMP_ADD_ICON_SIZE,
                                        height=STAMP_ADD_ICON_SIZE,
                                        padding=0,
                                        hover_color=ft.Colors.TRANSPARENT,
                                        style=ft.ButtonStyle(
                                            color={
                                                ft.ControlState.DEFAULT: GREY_700,
                                                ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                                            },
                                            overlay_color=ft.Colors.TRANSPARENT,
                                        ),
                                        on_click=self._handle_add_stamp,
                                        tooltip=_("stamps.add_tooltip"),
                                    ),
                                ],
                                height=_ADD_STAMP_CARD_HEIGHT,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
                col={"sm": 6, "md": 3},
            )
        )

        return ft.ResponsiveRow(
            controls=stamp_controls,
            run_spacing=12,
        )

    def _handle_add_stamp(self, e: ft.ControlEvent) -> None:
        if self._on_add_stamp:
            self._on_add_stamp(e)
