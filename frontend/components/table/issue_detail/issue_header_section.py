"""Header section — issue name, valuation badges, action icons."""

import datetime
from typing import Callable, Optional

import flet as ft

from components.colors import GREY_700
from components.form.date_picker import DatePickerField
from core.translations import _
from components.constants import (
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XLARGE,
    ISSUE_ACTION_ICON_SIZE,
)
from components.table.column_def import fmt_currency, fmt_date, fmt_number


class IssueHeaderSection(ft.Container):
    """Issue identity header with name, valuation badges, and action icons.

    Displays the series name (editable via ``ft.TextField`` in edit mode),
    emission date, mint/used/total-printed badges, and four action icons
    (edit, save, cancel, delete). Icon toggling and name editing are
    managed through ``enter_edit_mode`` / ``exit_edit_mode``.

    Args:
        issue: Issue data dict.
        lang: Language code (``"en"`` or ``"es"``).
        on_edit_click: Fired when the edit icon is clicked.
        on_delete_click: Fired when the delete icon is clicked.
        on_save_click: Fired when the save icon is clicked.
        on_cancel_click: Fired when the cancel icon is clicked.
    """

    def __init__(
        self,
        issue: dict,
        lang: str,
        on_edit_click: Optional[Callable] = None,
        on_delete_click: Optional[Callable] = None,
        on_save_click: Optional[Callable] = None,
        on_cancel_click: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._issue: dict = issue
        self._lang: str = lang
        self._on_edit_click: Optional[Callable] = on_edit_click
        self._on_delete_click: Optional[Callable] = on_delete_click
        self._on_save_click: Optional[Callable] = on_save_click
        self._on_cancel_click: Optional[Callable] = on_cancel_click

        self._original_name: str = self._issue.get("name") or _("ui.no_text_value")
        raw_mint = self._issue.get("market_value_mnh")
        self._original_mint: str = str(raw_mint) if raw_mint is not None else "0"
        raw_used = self._issue.get("market_value_used")
        self._original_used: str = str(raw_used) if raw_used is not None else "0"
        raw_total = self._issue.get("total_printed")
        self._original_total_printed: str = str(raw_total) if raw_total is not None else "0"
        self._name_container: ft.Container = self._build_name_control()
        self._name_textfield: Optional[ft.TextField] = None
        self._mint_value_container: Optional[ft.Container] = None
        self._mint_textfield: Optional[ft.TextField] = None
        self._used_value_container: Optional[ft.Container] = None
        self._used_textfield: Optional[ft.TextField] = None
        self._total_printed_container: Optional[ft.Container] = None
        self._total_printed_textfield: Optional[ft.TextField] = None
        raw_date = self._issue.get("date", "")
        self._original_date: str = raw_date if raw_date else ""
        self._date_container: Optional[ft.Container] = None
        self._date_picker_field: Optional[DatePickerField] = None
        self._edit_icon: ft.IconButton = self._new_icon(
            ft.Icons.EDIT, _("issues.edit_tooltip"), ft.Colors.ORANGE_700, True, self._on_edit_click
        )
        self._save_icon: ft.IconButton = self._new_icon(
            ft.Icons.CHECK, _("issues.save_tooltip"), ft.Colors.GREEN_700, False, self._on_save_click
        )
        self._cancel_icon: ft.IconButton = self._new_icon(
            ft.Icons.CLOSE, _("ui.cancel"), ft.Colors.RED_700, False, self._on_cancel_click
        )
        self._delete_icon: ft.IconButton = self._new_icon(
            ft.Icons.DELETE, _("issues.delete_tooltip"), ft.Colors.RED_700, True, self._on_delete_click
        )

        self.content = self._build_content()

    def _new_icon(self, icon: str, tooltip: str, hover_color: str, visible: bool, on_click) -> ft.IconButton:
        s = ISSUE_ACTION_ICON_SIZE
        return ft.IconButton(
            icon=icon,
            icon_size=s,
            splash_radius=1,
            splash_color=ft.Colors.TRANSPARENT,
            width=s,
            height=s,
            padding=0,
            hover_color=ft.Colors.TRANSPARENT,
            visible=visible,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: GREY_700,
                    ft.ControlState.HOVERED: hover_color,
                },
                overlay_color=ft.Colors.TRANSPARENT,
            ),
            tooltip=tooltip,
            on_click=on_click,
        )

    def _build_name_control(self) -> ft.Container:
        return ft.Container(
            content=ft.Text(
                self._original_name,
                size=FONT_SIZE_XLARGE,
                font_family="Roboto-Black",
            ),
        )

    def _build_content(self) -> ft.Column:
        issue = self._issue
        mint_value: float = float(issue.get("market_value_mnh") or 0)
        used_value: float = float(issue.get("market_value_used") or 0)
        total_printed: int = int(issue.get("total_printed") or 0)

        mint_badge = self._badge(
            _("stamps.mint"),
            fmt_currency(mint_value, self._lang),
            ft.Colors.GREEN_100,
            ft.Colors.GREEN_700,
        )
        self._mint_value_container = mint_badge.controls[1]

        used_badge = self._badge(
            _("stamps.used"),
            fmt_currency(used_value, self._lang),
            ft.Colors.BLUE_100,
            ft.Colors.BLUE_700,
        )
        self._used_value_container = used_badge.controls[1]

        total_printed_badge = self._badge(
            _("stamps.total_printed"),
            fmt_number(total_printed, self._lang),
            ft.Colors.GREY_300,
            None,
        )
        self._total_printed_container = total_printed_badge.controls[1]

        self._date_container = ft.Container(
            content=ft.Text(
                fmt_date(issue.get("date", ""), self._lang),
                size=FONT_SIZE_SMALL_HEADING,
                color=GREY_700,
            ),
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._name_container,
                        ft.Row(
                            controls=[
                                mint_badge,
                                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                used_badge,
                                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                                total_printed_badge,
                            ],
                            spacing=16,
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                self._edit_icon,
                                self._save_icon,
                                self._cancel_icon,
                                self._delete_icon,
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=0,
                        ),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._date_container,
            ],
            spacing=4,
        )

    def _badge(self, label: str, value: str, bgcolor: str, text_color: Optional[str]) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Text(label, size=FONT_SIZE_DEFAULT, font_family="Roboto-Black", color=GREY_700),
                ft.Container(
                    content=ft.Text(value, size=FONT_SIZE_DEFAULT, font_family="Roboto-Black",
                                    color=text_color or ft.Colors.BLACK_87),
                    bgcolor=bgcolor,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                ),
            ],
            spacing=6,
        )

    # --- Edit mode helpers ---

    def enter_edit_mode(self, hint_text: str, page: Optional[ft.Page] = None) -> None:
        self._name_textfield = ft.TextField(
            value=self._issue.get("name") or self._original_name,
            hint_text=hint_text,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_XLARGE, font_family="Roboto-Black"),
            content_padding=ft.Padding(0, 0, 0, 0),
        )
        self._name_container.content = self._name_textfield

        current_mint_raw = self._issue.get("market_value_mnh") or self._original_mint
        self._mint_textfield = ft.TextField(
            value=str(current_mint_raw) if current_mint_raw != "0" else "",
            hint_text="0.00",
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto-Black",
                                     color=ft.Colors.GREEN_700),
            content_padding=ft.Padding(0, 0, 0, 0),
            width=80,
            keyboard_type="number",
        )
        self._mint_value_container.content = self._mint_textfield

        current_used_raw = self._issue.get("market_value_used") or self._original_used
        self._used_textfield = ft.TextField(
            value=str(current_used_raw) if current_used_raw != "0" else "",
            hint_text="0.00",
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto-Black",
                                     color=ft.Colors.BLUE_700),
            content_padding=ft.Padding(0, 0, 0, 0),
            width=80,
            keyboard_type="number",
        )
        self._used_value_container.content = self._used_textfield

        current_total_raw = self._issue.get("total_printed") or self._original_total_printed
        self._total_printed_textfield = ft.TextField(
            value=str(current_total_raw) if current_total_raw != "0" else "",
            hint_text="0",
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto-Black"),
            content_padding=ft.Padding(0, 0, 0, 0),
            width=80,
            keyboard_type="number",
        )
        self._total_printed_container.content = self._total_printed_textfield

        if page is not None:
            date_str: str = self._issue.get("date") or self._original_date
            initial_date: Optional[datetime.date] = None
            if date_str:
                try:
                    initial_date = datetime.date.fromisoformat(date_str)
                except ValueError:
                    initial_date = None
            self._date_picker_field = DatePickerField(
                page=page,
                label="",
                value=initial_date,
                width=160,
                dense=True,
            )
            self._date_container.content = self._date_picker_field

        self._edit_icon.visible = False
        self._delete_icon.visible = False
        self._save_icon.visible = True
        self._cancel_icon.visible = True
        self._safe_update()

    def exit_edit_mode(self, saved: bool, new_name: str = "") -> None:
        name_display = new_name if saved else self._original_name
        self._name_container.content = ft.Text(
            name_display,
            size=FONT_SIZE_XLARGE,
            font_family="Roboto-Black",
        )
        self._name_textfield = None

        if saved:
            mint_raw = self._issue.get("market_value_mnh", self._original_mint)
        else:
            mint_raw = self._original_mint
        mint_display = fmt_currency(float(mint_raw), self._lang)
        self._mint_value_container.content = ft.Text(
            mint_display,
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto-Black",
            color=ft.Colors.GREEN_700,
        )
        self._mint_textfield = None

        if saved:
            used_raw = self._issue.get("market_value_used", self._original_used)
        else:
            used_raw = self._original_used
        used_display = fmt_currency(float(used_raw), self._lang)
        self._used_value_container.content = ft.Text(
            used_display,
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto-Black",
            color=ft.Colors.BLUE_700,
        )
        self._used_textfield = None

        if saved:
            total_raw = self._issue.get("total_printed", self._original_total_printed)
        else:
            total_raw = self._original_total_printed
        total_display = fmt_number(int(float(total_raw)), self._lang)
        self._total_printed_container.content = ft.Text(
            total_display,
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto-Black",
        )
        self._total_printed_textfield = None

        if saved:
            date_raw = self._issue.get("date", self._original_date)
        else:
            date_raw = self._original_date
        date_display = fmt_date(date_raw, self._lang) if date_raw else ""
        self._date_container.content = ft.Text(
            date_display,
            size=FONT_SIZE_SMALL_HEADING,
            color=GREY_700,
        )
        self._date_picker_field = None

        self._edit_icon.visible = True
        self._delete_icon.visible = True
        self._save_icon.visible = False
        self._cancel_icon.visible = False
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except RuntimeError:
            pass

    @property
    def name_text(self) -> str:
        if self._name_textfield is not None:
            return self._name_textfield.value.strip()
        return self._original_name

    @property
    def mint_value(self) -> float:
        if self._mint_textfield is not None:
            try:
                return float(self._mint_textfield.value.strip() or "0")
            except ValueError:
                return 0.0
        return float(self._issue.get("market_value_mnh") or 0)

    @property
    def used_value(self) -> float:
        if self._used_textfield is not None:
            try:
                return float(self._used_textfield.value.strip() or "0")
            except ValueError:
                return 0.0
        return float(self._issue.get("market_value_used") or 0)

    @property
    def total_printed_value(self) -> int:
        if self._total_printed_textfield is not None:
            try:
                return int(float(self._total_printed_textfield.value.strip() or "0"))
            except ValueError:
                return 0
        return int(self._issue.get("total_printed") or 0)

    @property
    def date_value(self) -> str:
        if self._date_picker_field is not None:
            d = self._date_picker_field.value
            return d.isoformat() if d else ""
        return self._original_date
