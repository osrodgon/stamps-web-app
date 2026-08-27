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
    """AlertDialog-based form for creating or editing a stamp.

    Layout mirrors ``show_stamp_detail_dialog`` — same Card, same Row
    structure, same spacing — but each display element is replaced with
    an ``ft.TextField`` using ``hint_text`` to indicate what to enter.

    When ``stamp_data`` is provided, the form operates in edit mode:
    fields are pre-populated and the save action calls ``update_stamp()``
    instead of ``create_stamp()``.

    Attributes:
        page: The Flet page instance.
        _service: The IssueService for API calls.
        _issue_id: The ID of the parent issue.
        _stamp_data: Stamp dict for edit mode (None for create mode).
        _on_success: Callback fired after successful save (sync only).
    """

    def __init__(
        self,
        page: ft.Page,
        issue_service: IssueService,
        issue_id: int,
        stamp_data: Optional[dict] = None,
        on_success: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page: ft.Page = page
        self._service: IssueService = issue_service
        self._issue_id: int = issue_id
        self._stamp_data: Optional[dict] = stamp_data
        self._on_success: Optional[Callable[[], None]] = on_success

        self._editing: bool = stamp_data is not None
        self._stamp_id: Optional[int] = stamp_data.get("id") if stamp_data else None

        self._dlg: Optional[ft.AlertDialog] = None
        self._colors_list: list[dict] = []
        self._selected_colors: list[dict] = []

        # Color picker dialog state
        self._color_dialog: Optional[ft.AlertDialog] = None
        self._color_search: Optional[ft.TextField] = None
        self._color_checkboxes: list[ft.Checkbox] = []
        self._color_checkbox_col: Optional[ft.Column] = None

        # Fields
        self._name_field: Optional[ft.TextField] = None
        self._fesofi_field: Optional[ft.TextField] = None
        self._edifil_field: Optional[ft.TextField] = None
        self._face_value_field: Optional[ft.TextField] = None
        self._select_colors_btn: Optional[DefaultButton] = None
        self._color_chips: Optional[ft.Row] = None
        self._mnh_field: Optional[ft.TextField] = None
        self._used_field: Optional[ft.TextField] = None
        self._total_printed_field: Optional[ft.TextField] = None
        self._description_field: Optional[ft.TextField] = None

    # --- Lifecycle ---

    async def show(self) -> None:
        """Fetch colors reference data and display the form dialog."""
        title_key: str = "stamps.edit_title" if self._editing else "stamps.create_title"
        title_text: str = _("stamps.edit_title") if self._editing and _("stamps.edit_title") != "stamps.edit_title" else _("stamps.create_title") if _("stamps.create_title") != "stamps.create_title" else "Stamp"
        self._dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                title_text,
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
                raw: list[dict] = colors_response.json().get("data", [])
                self._colors_list = sorted(raw, key=lambda x: x.get("name", "").lower())
            except Exception:
                self._colors_list = []
        else:
            self._colors_list = []

        # Pre-populate colors in edit mode
        if self._editing and self._stamp_data:
            stamp_color_names: list[str] = self._stamp_data.get("colors", [])
            self._selected_colors = [
                c for c in self._colors_list
                if c["name"] in stamp_color_names
            ]

        self._build_content()
        self.page.update()

    def _stamp_value(self, key: str, default: str = "") -> str:
        """Return a stamp data value for pre-population, or default.

        Args:
            key: The dict key in ``_stamp_data``.
            default: Fallback value when not editing or key is missing.

        Returns:
            The string value to set on a TextField.
        """
        if not self._editing or self._stamp_data is None:
            return default
        val = self._stamp_data.get(key)
        return str(val) if val is not None else default

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
            value=self._stamp_value("name"),
            hint_text=_("stamps.name"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
            dense=True,
            expand=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto-Black"),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._fesofi_field = ft.TextField(
            value=self._stamp_value("fesofi_code"),
            hint_text=_("stamps.fesofi_code"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
            dense=True,
            width=110,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._edifil_field = ft.TextField(
            value=self._stamp_value("edifil_code"),
            hint_text=_("stamps.edifil_code"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
            dense=True,
            width=110,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._face_value_field = ft.TextField(
            value=self._stamp_value("face_value"),
            hint_text=_("stamps.face_value"),
            hint_style=hint_style,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
            dense=True,
            expand=True,
            text_style=field_font,
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._select_colors_btn = PrimaryButton(
            text=_("stamps.select_colors") if _("stamps.select_colors") != "stamps.select_colors" else "Select Colors",
            on_click=lambda e: self._show_color_picker(),
            expand=False,
        )
        self._color_chips = ft.Row(
            controls=[],
            wrap=True,
            spacing=4,
            run_spacing=4,
        )
        prefix_style: ft.TextStyle = ft.TextStyle(
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto",
            color=GREY_700,
            italic=False,
        )
        self._mnh_field = ft.TextField(
            value=self._stamp_value("market_value_mnh"),
            hint_text="0.00",
            hint_style=hint_style,
            prefix="€ ",
            prefix_style=prefix_style,
            border=ft.InputBorder.NONE,
            dense=True,
            width=100,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._used_field = ft.TextField(
            value=self._stamp_value("market_value_used"),
            hint_text="0.00",
            hint_style=hint_style,
            prefix="€ ",
            prefix_style=prefix_style,
            border=ft.InputBorder.NONE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._total_printed_field = ft.TextField(
            value=self._stamp_value("total_printed"),
            hint_text="0",
            hint_style=hint_style,
            border=ft.InputBorder.NONE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto", color=GREY_700),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._description_field = ft.TextField(
            value=self._stamp_value("description"),
            hint_text=_("common.description"),
            hint_style=hint_style,
            multiline=True,
            min_lines=2,
            max_lines=6,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
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
                    #ft.Text(f"{_('stamps.color')}: ", **_ls()),
                    self._select_colors_btn,
                    self._color_chips,
                ],
                spacing=2,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{_('stamps.mint')}: ", **_ls()),
                                ft.Container(content=self._mnh_field, width=100),
                            ],
                            spacing=2,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor=ft.Colors.GREEN_100,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                width=200
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{_('stamps.used')}: ", **_ls()),
                                ft.Container(content=self._used_field, width=100),
                            ],
                            spacing=2,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor=ft.Colors.BLUE_100,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                width=200
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{_('stamps.total_printed')}: ", **_ls()),
                                ft.Container(content=self._total_printed_field, width=100),
                            ],
                            spacing=2,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor=ft.Colors.GREY_300,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                width=200,
            ),
        ]

        cancel_btn = DefaultButton(
            text=_("ui.cancel").upper(),
            on_click=self._on_cancel,
            expand=False,
        )
        create_btn = PrimaryButton(
            text=(
                _("stamps.update_stamp")
                if self._editing and _("stamps.update_stamp") != "stamps.update_stamp"
                else _("stamps.create_stamp")
                if _("stamps.create_stamp") != "stamps.create_stamp"
                else "Save"
            ).upper(),
            on_click=self._on_save,
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
                                            _("common.description").upper(),
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

        if self._editing:
            self._rebuild_chips(page_not_ready=True)

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

    # --- Color picker dialog ---

    def _show_color_picker(self) -> None:
        """Open a searchable multi-select dialog for picking colors."""
        self._color_search = ft.TextField(
            hint_text=_("stamps.search_colors") if _("stamps.search_colors") != "stamps.search_colors" else "Search colors...",
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            on_change=self._filter_color_checkboxes,
        )
        self._color_checkboxes = [
            ft.Checkbox(
                label=c["name"],
                value=any(sc["id"] == c["id"] for sc in self._selected_colors),
            )
            for c in sorted(self._colors_list, key=lambda x: x["name"])
        ]
        checkbox_col = ft.Column(
            controls=self._color_checkboxes,
            spacing=0,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            height=300,
        )
        self._color_checkbox_col = checkbox_col
        cancel_btn = DefaultButton(
            text=_("ui.cancel").upper(),
            on_click=lambda e: self._close_color_picker(),
            expand=False,
        )
        done_btn = PrimaryButton(
            text=_("ui.done").upper() if _("ui.done") != "ui.done" else "Done",
            on_click=lambda e: self._apply_colors(),
            expand=False,
        )
        self._color_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("stamps.select_colors") if _("stamps.select_colors") != "stamps.select_colors" else "Select Colors", font_family="Roboto-Black"),
            content=ft.Column(
                controls=[
                    self._color_search,
                    ft.Divider(height=1),
                    checkbox_col,
                ],
                tight=True,
                width=320,
            ),
            actions=[
                ft.Row(
                    controls=[cancel_btn, done_btn],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._color_dialog)
        self._color_dialog.open = True
        self.page.update()

    def _close_color_picker(self) -> None:
        """Close the color picker dialog."""
        if self._color_dialog:
            self._color_dialog.open = False
            self.page.update()

    def _filter_color_checkboxes(self, e: ft.ControlEvent) -> None:
        """Filter color checkboxes by search text."""
        query: str = (e.data or "").strip().lower()
        for cb in self._color_checkboxes:
            cb.visible = not query or query in cb.label.lower()
        if self._color_checkbox_col:
            self._color_checkbox_col.update()

    def _apply_colors(self) -> None:
        """Read checked colors and update selected_colors chips."""
        self._selected_colors = [
            c for c in self._colors_list
            if any(
                cb.label == c["name"] and cb.value
                for cb in self._color_checkboxes
            )
        ]
        self._rebuild_chips()
        self._close_color_picker()

    def _rebuild_chips(self, page_not_ready: bool = False) -> None:
        """Rebuild the chip row from the selected colors list.

        Args:
            page_not_ready: If True, skip the ``update()`` call since
                the control is not yet attached to the page tree.
        """
        chips: list[ft.Control] = []
        for c in self._selected_colors:
            chip = ft.Chip(
                label=ft.Text(c["name"], size=13),
                delete_icon=ft.Icon(ft.Icons.CLOSE, size=16),
                on_delete=lambda _, cid=c["id"]: self._remove_color(cid),
                bgcolor=ft.Colors.GREY_200,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )
            chips.append(chip)
        self._color_chips.controls = chips
        if not page_not_ready:
            self._color_chips.update()

    def _remove_color(self, color_id: int) -> None:
        """Remove a color from the selected list and rebuild chips.

        Args:
            color_id: The ID of the color to remove.
        """
        self._selected_colors = [c for c in self._selected_colors if c["id"] != color_id]
        self._rebuild_chips()

    # --- Color resolution ---

    def _resolve_color_ids(self) -> list[int]:
        """Return the list of selected color IDs.

        Returns:
            List of color IDs from the selected chips.
        """
        return [c["id"] for c in self._selected_colors]

    async def _on_save(self, e: ft.ControlEvent) -> None:
        """Validate and submit the form.

        In create mode, calls ``create_stamp()``.
        In edit mode, calls ``update_stamp()``.

        Args:
            e: The click event from the Save button.
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

        color_ids: list[int] = self._resolve_color_ids()

        payload: dict[str, Any] = {
            "name": name_val,
            "face_value": face_val,
        }

        if not self._editing:
            payload["issue"] = self._issue_id

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

        self.log.debug(f"Saving stamp with payload: {payload}")
        try:
            if self._editing and self._stamp_id is not None:
                response = await self._service.update_stamp(self._stamp_id, payload)
            else:
                response = await self._service.create_stamp(payload)
            if response and response.status_code in (200, 201):
                self.close()
                if self._on_success:
                    self._on_success()
                await self.show_notification(
                    _("stamps.update_success") if self._editing
                    else _("stamps.creation_success"),
                    severity=Severity.SUCCESS,
                )
            else:
                error_msg = (
                    _("stamps.update_failed") if self._editing
                    else _("stamps.creation_failed")
                )
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_msg)
                    except Exception:
                        pass
                self.log.error(f"Failed to save stamp: {error_msg}")
                await self.show_notification(error_msg, severity=Severity.ERROR)
        except Exception as exc:
            self.log.error(f"{exc}")
            await self.show_notification(
                _("issues.network_error"), severity=Severity.ERROR
            )
