"""AlertDialog-based form for creating a new stamp.

Layout matches ``stamp_detail_dialog`` exactly: image placeholder on the
left, editable fields on the right (replacing read-only texts/badges),
divider, and a multiline description field.
"""

from typing import Any, Callable, Optional

import flet as ft
import requests

from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.colors import DARK_IMG_BG, GREY_700
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_PADDING,
    DIALOG_WIDTH,
    DIALOG_IMAGE_MAX_HEIGHT,
    FONT_SIZE_DEFAULT,
)
from core.base_ui import BaseUI
from core.severity import Severity
from core.logger import Logger
from core.translations import _, get_language
from services.issue_service import IssueService


class StampForm(BaseUI, Logger):
    """AlertDialog-based form for creating a new stamp.

    Layout mirrors ``show_stamp_detail_dialog`` — same Card, same Row
    structure, same spacing — but each display element is replaced with
    an ``ft.TextField`` using ``hint_text`` to indicate what to enter.

    Attributes:
        page: The Flet page instance.
        _service: The IssueService for API calls.
        _issue_id: The ID of the parent issue to add the stamp to.
        _on_success: Callback fired after successful creation (sync only).
    """

    def __init__(
        self,
        page: ft.Page,
        issue_service: IssueService,
        issue_id: int,
        on_success: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page: ft.Page = page
        self._service: IssueService = issue_service
        self._issue_id: int = issue_id
        self._on_success: Optional[Callable[[], None]] = on_success

        self._dlg: Optional[ft.AlertDialog] = None
        self._colors_list: list[dict] = []

        # Fields
        self._name_field: Optional[ft.TextField] = None
        self._fesofi_field: Optional[ft.TextField] = None
        self._edifil_field: Optional[ft.TextField] = None
        self._face_value_field: Optional[ft.TextField] = None
        self._colors_field: Optional[ft.TextField] = None
        self._color_picker: Optional[ft.Dropdown] = None
        self._mnh_field: Optional[ft.TextField] = None
        self._used_field: Optional[ft.TextField] = None
        self._total_printed_field: Optional[ft.TextField] = None
        self._description_field: Optional[ft.TextField] = None

    # --- Lifecycle ---

    async def show(self) -> None:
        """Fetch colors reference data and display the form dialog."""
        self._dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                _("stamps.create_title") if _("stamps.create_title") != "stamps.create_title" else "Create Stamp",
                size=23,
                font_family="Roboto-Black",
                margin=ft.Margin(left=12),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(height=200),
                    ft.Row(
                        controls=[ft.ProgressRing()],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                width=DIALOG_WIDTH,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dlg)
        self._dlg.open = True
        self.page.update()

        # Fetch colors
        colors_response = await self._service.get_colors()
        if colors_response and colors_response.status_code == requests.codes.ok:
            try:
                self._colors_list = colors_response.json().get("data", [])
            except Exception:
                self._colors_list = []
        else:
            self._colors_list = []

        self._build_content()
        self.page.update()

    def _build_content(self) -> None:
        """Replace the loading spinner with the form layout matching stamp_detail_dialog."""
        field_font: ft.TextStyle = ft.TextStyle(
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto",
        )
        hint_style: ft.TextStyle = ft.TextStyle(
            color=GREY_700, italic=True, size=FONT_SIZE_DEFAULT
        )
        self._name_field = ft.TextField(
            value="",
            hint_text=_("stamps.name"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto-Black"),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._fesofi_field = ft.TextField(
            value="",
            hint_text=_("stamps.fesofi_code"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            width=110,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._edifil_field = ft.TextField(
            value="",
            hint_text=_("stamps.edifil_code"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            width=110,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._face_value_field = ft.TextField(
            value="",
            hint_text=_("stamps.face_value"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        sorted_colors: list[dict] = sorted(
            self._colors_list, key=lambda x: x["name"].lower()
        )
        self._colors_field = ft.TextField(
            value="",
            hint_text=_("stamps.color"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._color_picker = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=str(c["id"]), text=c["name"])
                for c in sorted_colors
            ],
            hint_text=_("stamps.select_color"),
            dense=True,
            expand=False,
            width=180,
            on_select=self._on_color_select,
        )
        self._mnh_field = ft.TextField(
            value="",
            hint_text="0.00",
            hint_style=hint_style,
            border=ft.InputBorder.NONE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._used_field = ft.TextField(
            value="",
            hint_text="0.00",
            hint_style=hint_style,
            border=ft.InputBorder.NONE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._total_printed_field = ft.TextField(
            value="",
            hint_text="0",
            hint_style=hint_style,
            border=ft.InputBorder.NONE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._description_field = ft.TextField(
            value="",
            hint_text=_("stamps.description"),
            hint_style=hint_style,
            multiline=True,
            min_lines=2,
            max_lines=6,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=field_font,
        )

        _ls = lambda: dict(size=FONT_SIZE_DEFAULT, color=GREY_700)

        # Build right-column controls matching stamp_detail_dialog layout order
        right_controls: list[ft.Control] = [
            self._name_field,
            ft.Row(
                controls=[
                    ft.Text("FESOFI: ", **_ls()),
                    self._fesofi_field,
                    ft.Text(" | Edifil: ", **_ls()),
                    self._edifil_field,
                ],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Text(f"{_('stamps.face_value')}: ", **_ls()),
                    self._face_value_field,
                ],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Text(f"{_('stamps.color')}: ", **_ls()),
                    self._colors_field,
                    self._color_picker,
                ],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(f"{_('stamps.mint')}: ", **_ls()),
                        self._mnh_field,
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                bgcolor=ft.Colors.GREEN_100,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                expand=False,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(f"{_('stamps.used')}: ", **_ls()),
                        self._used_field,
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                bgcolor=ft.Colors.BLUE_100,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                expand=False,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(f"{_('stamps.total_printed')}: ", **_ls()),
                        self._total_printed_field,
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                bgcolor=ft.Colors.GREY_300,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                expand=False,
            ),
        ]

        cancel_btn = DefaultButton(
            text=_("ui.cancel").upper(),
            on_click=self._on_cancel,
            expand=False,
        )
        create_btn = PrimaryButton(
            text=(
                _("stamps.create_stamp")
                if _("stamps.create_stamp") != "stamps.create_stamp"
                else "Create Stamp"
            ).upper(),
            on_click=self._on_create,
            expand=False,
        )

        content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Card(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        # Left: image placeholder
                                        ft.Container(
                                            content=ft.Column(
                                                controls=[
                                                    ft.Icon(
                                                        ft.Icons.CAMERA_ALT_OUTLINED,
                                                        size=48,
                                                        color=ft.Colors.WHITE_54,
                                                    ),
                                                    ft.Text(
                                                        "",
                                                        size=FONT_SIZE_DEFAULT,
                                                        color=ft.Colors.WHITE_54,
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                expand=True,
                                            ),
                                            bgcolor=DARK_IMG_BG,
                                            height=DIALOG_IMAGE_MAX_HEIGHT,
                                            width=DIALOG_IMAGE_MAX_HEIGHT,
                                            border_radius=4,
                                            shadow=ft.BoxShadow(
                                                blur_radius=4,
                                                color=ft.Colors.BLACK_26,
                                                offset=ft.Offset(1, 2),
                                            ),
                                        ),
                                        # Right: editable fields matching detail dialog layout
                                        ft.Column(
                                            controls=right_controls,
                                            spacing=8,
                                            expand=True,
                                            margin=ft.Margin(left=12),
                                        ),
                                    ],
                                ),
                                ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            _("ui.description").upper(),
                                            size=FONT_SIZE_DEFAULT,
                                            font_family="Roboto-Black",
                                            color=GREY_700,
                                        ),
                                        self._description_field,
                                    ],
                                    spacing=4,
                                ),
                            ],
                            spacing=16,
                            margin=ft.Margin(left=12, right=12, top=12, bottom=12),
                        ),
                    ),
                    ft.Row(
                        controls=[cancel_btn, create_btn],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=12,
                    ),
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=DIALOG_WIDTH,
        )

        if self._dlg:
            self._dlg.content = content

    def close(self) -> None:
        """Close the dialog and clean up."""
        if self._dlg:
            self._dlg.open = False
            self.page.update()

    # --- Event handlers ---

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Close the form dialog without saving.

        Args:
            e: The click event from the Cancel button.
        """
        self.close()

    # --- Color picker ---

    def _on_color_select(self, e: ft.ControlEvent) -> None:
        """Append the selected color to the comma-separated colors field.

        Args:
            e: The select event from the color picker dropdown.
        """
        if not e.data:
            return
        selected_name: str = ""
        for opt in self._color_picker.options:
            if opt.key == e.data:
                selected_name = opt.text
                break
        if not selected_name:
            return

        current: str = self._colors_field.value or ""
        if current.strip():
            self._colors_field.value = current.rstrip(", ") + ", " + selected_name
        else:
            self._colors_field.value = selected_name
        self._color_picker.value = None
        self._color_picker.update()
        self._colors_field.update()

    # --- Color resolution ---

    def _resolve_color_ids(self, colors_str: str) -> list[int]:
        """Parse comma-separated color names and return a list of IDs.

        Args:
            colors_str: Comma-separated color names.

        Returns:
            List of matching color IDs.
        """
        if not colors_str:
            return []
        parts: list[str] = [p.strip() for p in colors_str.split(",") if p.strip()]
        if not parts:
            return []
        name_to_id: dict[str, int] = {c["name"].strip().lower(): c["id"] for c in self._colors_list}
        ids: list[int] = []
        for part in parts:
            cid = name_to_id.get(part.lower())
            if cid is not None:
                ids.append(cid)
        return ids

    async def _on_create(self, e: ft.ControlEvent) -> None:
        """Validate and submit the form to create a new stamp.

        Args:
            e: The click event from the Create Stamp button.
        """
        self.log.debug("Validating required fields...")

        name_val: str = self._name_field.value.strip() if self._name_field else ""
        if not name_val:
            await self.show_notification(
                _("stamps.name_required") if _("stamps.name_required") != "stamps.name_required" else "Name is required",
                severity=Severity.ERROR,
            )
            return

        face_val: str = self._face_value_field.value.strip() if self._face_value_field else ""
        if not face_val:
            await self.show_notification(
                _("stamps.face_value_required") if _("stamps.face_value_required") != "stamps.face_value_required" else "Face value is required",
                severity=Severity.ERROR,
            )
            return

        fesofi_val: str = self._fesofi_field.value.strip() if self._fesofi_field else ""
        edifil_val: str = self._edifil_field.value.strip() if self._edifil_field else ""
        colors_str: str = self._colors_field.value.strip() if self._colors_field else ""

        mnh_raw: str = self._mnh_field.value.strip() if self._mnh_field else ""
        used_raw: str = self._used_field.value.strip() if self._used_field else ""
        total_raw: str = self._total_printed_field.value.strip() if self._total_printed_field else ""
        desc_val: str = self._description_field.value.strip() if self._description_field else ""

        mnh_val: Optional[float] = None
        used_val: Optional[float] = None
        total_val: Optional[int] = None

        if mnh_raw:
            try:
                mnh_val = float(mnh_raw)
            except (ValueError, TypeError):
                pass
        if used_raw:
            try:
                used_val = float(used_raw)
            except (ValueError, TypeError):
                pass
        if total_raw:
            try:
                total_val = int(total_raw)
            except (ValueError, TypeError):
                pass

        color_ids: list[int] = self._resolve_color_ids(colors_str)

        payload: dict[str, Any] = {
            "issue": self._issue_id,
            "name": name_val,
            "face_value": face_val,
        }

        if fesofi_val:
            payload["fesofi_code"] = fesofi_val
        if edifil_val:
            payload["edifil_code"] = edifil_val
        if mnh_val is not None:
            payload["market_value_mnh"] = str(mnh_val)
        if used_val is not None:
            payload["market_value_used"] = str(used_val)
        if total_val is not None:
            payload["total_printed"] = str(total_val)
        if desc_val:
            payload["description"] = desc_val
        if color_ids:
            payload["colors"] = color_ids

        self.log.debug(f"Creating stamp with payload: {payload}")
        try:
            response = await self._service.create_stamp(payload)
            if response and response.status_code in (200, 201):
                self.close()
                if self._on_success:
                    self._on_success()
                await self.show_notification(
                    _("stamps.creation_success") if _("stamps.creation_success") != "stamps.creation_success" else "Stamp created successfully",
                    severity=Severity.SUCCESS,
                )
            else:
                error_msg = (
                    _("stamps.creation_failed") if _("stamps.creation_failed") != "stamps.creation_failed" else "Failed to create stamp"
                )
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_msg)
                    except Exception:
                        pass
                self.log.error(f"Failed to create stamp: {error_msg}")
                await self.show_notification(error_msg, severity=Severity.ERROR)
        except Exception as exc:
            self.log.error(f"{exc}")
            await self.show_notification(
                _("issues.network_error"), severity=Severity.ERROR
            )
