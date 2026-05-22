"""Stamp card component — individual stamp thumbnail with catalog info."""

import os
from typing import Callable, Optional

import flet as ft

from components.colors import DARK_IMG_BG, GREY_700
from components.table.column_def import fmt_currency
from components.table.issue_detail.stamp_detail_dialog import show_stamp_detail_dialog
from core.translations import _
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP
from components.constants import STAMP_ACTION_ICON_SIZE, STAMP_THUMBNAIL_SIZE, FONT_SIZE_DEFAULT, CARD_ELEVATION


class StampCard(ft.Card):
    """A single stamp card with thumbnail, catalog info, and action icons.

    Displays a stamp image (160x160 with dark background), the stamp name
    with edit/delete icon buttons right-aligned, catalog codes (FESOFI,
    Edifil), face value, colors, and MNH/Used valuation badges. Clicking
    the image opens the full-size stamp detail dialog.

    Args:
        stamp: Stamp data dict from the API response.
        issue_year: The year of the parent issue (for image path resolution).
        lang: Language code ("en" or "es").
        on_edit: Called with stamp ID when the edit icon is clicked.
        on_delete: Called with stamp ID when the delete icon is clicked.
    """

    def __init__(
        self,
        stamp: dict,
        issue_year: str,
        lang: str,
        on_edit: Optional[Callable[[int], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
    ) -> None:
        super().__init__()
        self._stamp: dict = stamp
        self._issue_year: str = issue_year
        self._lang: str = lang
        self._on_edit: Optional[Callable[[int], None]] = on_edit
        self._on_delete: Optional[Callable[[int], None]] = on_delete

        self.elevation = CARD_ELEVATION

        colors_list: list[str] = stamp.get("colors", [])
        colors_str: str = ", ".join(colors_list) if colors_list else "-"
        fesofi_code: str = stamp.get("fesofi_code") or ""
        image_rel: str = os.path.join(
            os.path.relpath(IMAGE_DIR, ASSETS_DIR), issue_year, f"{fesofi_code}.webp"
        )
        image_path: str = (
            image_rel
            if os.path.exists(os.path.join(IMAGE_DIR, issue_year, f"{fesofi_code}.webp"))
            else NO_STAMP
        )

        stamp_mnh: float = float(stamp.get("market_value_mnh") or 0)
        stamp_used: float = float(stamp.get("market_value_used") or 0)

        codes_text: str = f"FESOFI: {fesofi_code} | Edifil: {stamp.get('edifil_code') or '-'}"
        face_value_text: str = f"{_('stamps.face_value')}: {stamp.get('face_value') or '-'}"
        color_text: str = f"{_('stamps.color')}: {colors_str}"
        mnh_part: str = f"{_('stamps.mint')}: {fmt_currency(stamp_mnh, lang)}"
        used_part: str = f"{_('stamps.used')}: {fmt_currency(stamp_used, lang)}"
        stamp_actions_icon_size: int = STAMP_ACTION_ICON_SIZE

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Image(
                                    src=image_path,
                                    fit="contain",
                                    height=STAMP_THUMBNAIL_SIZE,
                                    width=STAMP_THUMBNAIL_SIZE,
                                ),
                                height=STAMP_THUMBNAIL_SIZE,
                                width=STAMP_THUMBNAIL_SIZE,
                                bgcolor=DARK_IMG_BG,
                                border_radius=4,
                                shadow=ft.BoxShadow(
                                    blur_radius=4,
                                    color=ft.Colors.BLACK_26,
                                    offset=ft.Offset(1, 2),
                                ),
                                on_click=self._show_detail,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                stamp.get("name") or "-",
                                                size=15,
                                                font_family="Roboto-Black",
                                                no_wrap=True,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                                expand=True,
                                            ),
                                            ft.Row(
                                                controls=[
                                                    ft.IconButton(
                                                        icon=ft.Icons.EDIT,
                                                        icon_size=stamp_actions_icon_size,
                                                        splash_radius=1,
                                                        splash_color=ft.Colors.TRANSPARENT,
                                                        width=stamp_actions_icon_size,
                                                        height=stamp_actions_icon_size,
                                                        padding=0,
                                                        hover_color=ft.Colors.TRANSPARENT,
                                                        style=ft.ButtonStyle(
                                                            color={
                                                                ft.ControlState.DEFAULT: GREY_700,
                                                                ft.ControlState.HOVERED: ft.Colors.ORANGE_700,
                                                            },
                                                            overlay_color=ft.Colors.TRANSPARENT,
                                                        ),
                                                        on_click=self._handle_edit,
                                                        tooltip=_("stamps.edit_tooltip")
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE,
                                                        icon_size=stamp_actions_icon_size,
                                                        splash_radius=1,
                                                        splash_color=ft.Colors.TRANSPARENT,
                                                        width=stamp_actions_icon_size,
                                                        height=stamp_actions_icon_size,
                                                        padding=0,
                                                        hover_color=ft.Colors.TRANSPARENT,
                                                        style=ft.ButtonStyle(
                                                            color={
                                                                ft.ControlState.DEFAULT: GREY_700,
                                                                ft.ControlState.HOVERED: ft.Colors.RED_700,
                                                            },
                                                            overlay_color=ft.Colors.TRANSPARENT,
                                                        ),
                                                        on_click=self._handle_delete,
                                                        tooltip=_("stamps.delete_tooltip")
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.END,
                                                spacing=0,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    ft.Text(codes_text, size=FONT_SIZE_DEFAULT, color=GREY_700, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(face_value_text, size=FONT_SIZE_DEFAULT, color=GREY_700, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(color_text, size=FONT_SIZE_DEFAULT, color=GREY_700, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Container(
                                        content=ft.Text(mnh_part, size=FONT_SIZE_DEFAULT, color=GREY_700, overflow=ft.TextOverflow.ELLIPSIS),
                                        bgcolor=ft.Colors.GREEN_100,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    ),
                                    ft.Container(
                                        content=ft.Text(used_part, size=FONT_SIZE_DEFAULT, color=GREY_700, overflow=ft.TextOverflow.ELLIPSIS),
                                        bgcolor=ft.Colors.BLUE_100,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    ),
                                ],
                                spacing=6,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    )
                ],
                spacing=4,
            ),
            padding=12,
            expand=True,
        )
        self.expand = True

    def _show_detail(self, e: ft.ControlEvent) -> None:
        show_stamp_detail_dialog(self.page, self._stamp, self._lang, self._issue_year)

    def _handle_edit(self, e: ft.ControlEvent) -> None:
        stamp_id = self._stamp.get("id")
        if self._on_edit and stamp_id is not None:
            self._on_edit(stamp_id)

    def _handle_delete(self, e: ft.ControlEvent) -> None:
        stamp_id = self._stamp.get("id")
        if self._on_delete and stamp_id is not None:
            self._on_delete(stamp_id)
