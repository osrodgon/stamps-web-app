"""Stamp detail dialog — standalone modal for full-size stamp image and metadata."""

import os
from typing import Optional

import flet as ft
from PIL import Image as PILImage

from components.buttons.default_button import DefaultButton
from components.colors import DARK_IMG_BG, GREY_700
from components.table.column_def import fmt_currency
from core.translations import _
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP


def show_stamp_detail_dialog(
    page: ft.Page,
    stamp: dict,
    lang: str,
    issue_year: str,
) -> None:
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

    abs_path: str = (
        os.path.join(ASSETS_DIR, NO_STAMP)
        if image_path == NO_STAMP
        else os.path.join(ASSETS_DIR, image_path)
    )
    try:
        display_height: int = min(PILImage.open(abs_path).height, 280)
    except Exception:
        display_height = 280

    stamp_mnh: float = float(stamp.get("market_value_mnh") or 0)
    stamp_used: float = float(stamp.get("market_value_used") or 0)
    description: str = stamp.get("description") or ""

    codes_text: str = f"FESOFI: {fesofi_code} | Edifil: {stamp.get('edifil_code') or '-'}"
    face_value_text: str = f"{_('stamps.face_value')}: {stamp.get('face_value') or '-'}"
    color_text: str = f"{_('stamps.color')}: {colors_str}"
    mnh_part: str = f"{_('stamps.mint')}: {fmt_currency(stamp_mnh, lang)}"
    used_part: str = f"{_('stamps.used')}: {fmt_currency(stamp_used, lang)}"

    def close(_: ft.ControlEvent | None = None) -> None:
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Card(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Image(
                                                src=image_path,
                                                fit="contain",
                                                height=display_height,
                                                width=display_height,
                                            ),
                                            bgcolor=DARK_IMG_BG,
                                            shadow=ft.BoxShadow(
                                                blur_radius=4,
                                                color=ft.Colors.BLACK_26,
                                                offset=ft.Offset(1, 2),
                                            ),
                                            border_radius=4,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(codes_text, size=14, color=GREY_700),
                                                ft.Text(face_value_text, size=14, color=GREY_700),
                                                ft.Text(color_text, size=14, color=GREY_700),
                                                ft.Container(
                                                    content=ft.Text(mnh_part, size=14, color=GREY_700),
                                                    bgcolor=ft.Colors.GREEN_100,
                                                    border_radius=6,
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                                ),
                                                ft.Container(
                                                    content=ft.Text(used_part, size=14, color=GREY_700),
                                                    bgcolor=ft.Colors.BLUE_100,
                                                    border_radius=6,
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                                ),
                                            ],
                                            spacing=8,
                                            expand=True,
                                            margin=ft.Margin(left=12),
                                        ),
                                    ]
                                ),
                                ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                                ft.Text(
                                    _("ui.description").upper(),
                                    size=14,
                                    font_family="Roboto-Black",
                                    color=GREY_700,
                                ),
                                ft.Text(
                                    description,
                                    size=15,
                                    font_family="Roboto",
                                    text_align=ft.TextAlign.JUSTIFY,
                                ),
                            ],
                            spacing=16,
                            margin=ft.Margin(left=12, right=12, top=12, bottom=12),
                        ),
                    )
                ],
                spacing=12,
                tight=True,
            ),
            width=700,
        ),
        actions=[DefaultButton(_("ui.close"), on_click=close)],
        on_dismiss=close,
        shape=ft.RoundedRectangleBorder(radius=8),
        title=ft.Text(
            stamp.get("name") or "-",
            size=23,
            font_family="Roboto-Black",
            margin=ft.Margin(left=12),
        ),
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()
