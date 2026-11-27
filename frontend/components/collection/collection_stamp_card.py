"""One stamp of a series with the user's copy (plan steps B4 and B5).

The card follows the mockup: a plate and the catalogue data on top, and the user's
copy underneath, separated by a hairline. The catalogue half is read-only —
codes, face value, colours and values — and the copy is the only part a normal
user can write.

The card never calls a service: it receives callbacks that return the item the API
saved (or None), and paints what came back. That keeps a refused write from leaving a
card that lies.
"""

from __future__ import annotations

import datetime
import os
from decimal import Decimal, InvalidOperation
from typing import Awaitable, Callable, Optional

import flet as ft

from components.buttons.action_icon import ActionIcon
from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.colors import (
    BG_ALT,
    GREY_700,
    MINT_BG,
    MINT_INK,
    RED,
    ROW_BORDER,
    USED_BG,
    USED_INK,
)
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_SHADOW_BLUR,
    CARD_SHADOW_OPACITY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XS,
)
from components.form.date_picker import DatePickerField
from components.form.dropdown import Dropdown
from components.form.text_field import TextField
from components.table.column_def import fmt_currency, fmt_date
from core.translations import _
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP


SaveCallback = Callable[[dict, int, dict], Awaitable[Optional[dict]]]
AddCallback = Callable[[dict], Awaitable[Optional[dict]]]
RemoveCallback = Callable[[int], Awaitable[bool]]


class CollectionStampCard(ft.Container):
    """A stamp of the series and the user's copy of it.

    Args:
        page: the Flet page, for the date picker and the dialogs.
        stamp: the detail row (stamp fields plus `item` or None).
        lang: the active language.
        condition_types: the conditions the copy can have, from the API.
        locations: the places it can be stored in.
        on_save: called with (stamp, item id, fields); returns the saved item.
        on_add: called with the stamp; returns the new item, or None.
        on_remove: called with the item id; returns True when it was deleted.
        on_changed: called after the item changes, so the page updates the summary.
    """

    PLATE_SIZE: int = 128
    CELLS_PER_ROW: int = 3

    def __init__(
        self,
        page: ft.Page,
        stamp: dict,
        lang: str,
        condition_types: Optional[list] = None,
        locations: Optional[list] = None,
        on_save: Optional[SaveCallback] = None,
        on_add: Optional[AddCallback] = None,
        on_remove: Optional[RemoveCallback] = None,
        on_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self._page: ft.Page = page
        self._stamp: dict = stamp
        self._lang: str = lang
        self._condition_types: list = condition_types or []
        self._locations: list = locations or []
        self._on_save: Optional[SaveCallback] = on_save
        self._on_add: Optional[AddCallback] = on_add
        self._on_remove: Optional[RemoveCallback] = on_remove
        self._on_changed: Optional[Callable[[], None]] = on_changed

        self._editing: bool = False
        self._confirm_dialog: Optional[ft.AlertDialog] = None
        self._item: Optional[dict] = stamp.get("item")
        self._image: ft.Image = self.__picture_control()
        self._copy_box: ft.Container = ft.Container(
            content=self.__copy_display(),
            border=ft.Border(top=ft.BorderSide(1, ROW_BORDER)),
            margin=ft.Margin.only(top=12),
            padding=ft.Padding.only(top=12),
        )

        self.content = ft.Column(
            controls=[self.__top(), self._copy_box],
            spacing=0,
            tight=True,
        )
        self.padding = ft.Padding.symmetric(horizontal=16, vertical=14)
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border.all(1, ROW_BORDER)
        self.border_radius = CARD_BORDER_RADIUS
        self.shadow = ft.BoxShadow(
            blur_radius=CARD_SHADOW_BLUR,
            color=ft.Colors.with_opacity(CARD_SHADOW_OPACITY, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        )
        self.__dim_copy()

    # ------------------------------------------------------------------
    # Catalogue (read-only)
    # ------------------------------------------------------------------

    def __top(self) -> ft.Row:
        """The plate and the catalogue data, side by side."""
        return ft.Row(
            controls=[
                ft.Container(
                    width=self.PLATE_SIZE,
                    height=self.PLATE_SIZE,
                    padding=4,
                    bgcolor=BG_ALT,
                    border_radius=CARD_BORDER_RADIUS,
                    alignment=ft.Alignment.CENTER,
                    content=self._image,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            self._stamp.get("name") or "",
                            size=FONT_SIZE_SMALL_HEADING,
                            weight=ft.FontWeight.BOLD,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        self.__codes(),
                        self.__data_line(
                            _("stamps.face_value"),
                            self._stamp.get("face_value") or "-",
                        ),
                        self.__data_line(
                            _("stamps.color"),
                            ", ".join(self._stamp.get("colors") or []) or "-",
                        ),
                        self.__pills(),
                    ],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def __picture_control(self) -> ft.Image:
        """The stamp's picture, or the placeholder."""
        year = self._stamp.get("issue_year")
        code = self._stamp.get("fesofi_code")
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
            width=self.PLATE_SIZE - 8,
            height=self.PLATE_SIZE - 8,
            fit=ft.BoxFit.CONTAIN,
            opacity=0.55 if faded else 1,
        )

    def __codes(self) -> ft.Text:
        """`FESOFI 0001 · Edifil 1`, with the labels muted."""
        return ft.Text(
            spans=[
                ft.TextSpan(
                    "FESOFI ",
                    ft.TextStyle(color=GREY_700, size=FONT_SIZE_XS),
                ),
                ft.TextSpan(
                    f"{self._stamp.get('fesofi_code') or '-'} · ",
                    ft.TextStyle(size=FONT_SIZE_XS),
                ),
                ft.TextSpan(
                    "Edifil ",
                    ft.TextStyle(color=GREY_700, size=FONT_SIZE_XS),
                ),
                ft.TextSpan(
                    self._stamp.get("edifil_code") or "-",
                    ft.TextStyle(size=FONT_SIZE_XS),
                ),
            ],
        )

    @staticmethod
    def __data_line(key: str, value: str) -> ft.Text:
        """A muted label and its value."""
        return ft.Text(
            spans=[
                ft.TextSpan(
                    f"{key} ",
                    ft.TextStyle(color=GREY_700, size=FONT_SIZE_XS),
                ),
                ft.TextSpan(str(value), ft.TextStyle(size=FONT_SIZE_XS)),
            ],
        )

    def __pills(self) -> ft.Row:
        """The catalogue values, as the mockup's pills."""
        return ft.Row(
            controls=[
                self.__pill(
                    _("stamps.mint"),
                    fmt_currency(self._stamp.get("market_value_mnh"), self._lang),
                    MINT_BG,
                    MINT_INK,
                ),
                self.__pill(
                    _("stamps.used"),
                    fmt_currency(self._stamp.get("market_value_used"), self._lang),
                    USED_BG,
                    USED_INK,
                ),
            ],
            spacing=8,
        )

    @staticmethod
    def __pill(label: str, value: str, background: str, ink: str) -> ft.Container:
        """One small coloured pill."""
        return ft.Container(
            content=ft.Text(
                f"{label} {value}",
                size=FONT_SIZE_XS,
                weight=ft.FontWeight.W_600,
                color=ink,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            bgcolor=background,
            border_radius=6,
        )

    # ------------------------------------------------------------------
    # Your copy
    # ------------------------------------------------------------------

    @property
    def item(self) -> Optional[dict]:
        """The copy the card currently shows, or None."""
        return self._item

    def set_item(self, item: Optional[dict]) -> None:
        """Adopt the item the API returned and paint it."""
        self._item = item
        self._stamp["item"] = item
        self._editing = False
        self._render_copy()
        if self._on_changed is not None:
            self._on_changed()

    def _render_copy(self) -> None:
        """Paint the display or the form, depending on the mode."""
        self._copy_box.content = (
            self.__copy_form() if self._editing else self.__copy_display()
        )
        self.__dim_copy()
        try:
            self.update()
        except RuntimeError:
            pass

    def __dim_copy(self) -> None:
        """A stamp the user does not own is shown dimmed, as the mockup does."""
        self._copy_box.opacity = 1 if self._item is not None else 0.62

    def __copy_display(self) -> ft.Control:
        """The copy's values, the edit link or the button to create it."""
        if self._item is None:
            return ft.Column(
                controls=[
                    ft.Text(
                        _("collections.no_copy"),
                        size=FONT_SIZE_XS,
                        color=GREY_700,
                    ),
                    DefaultButton(
                        text=_("collections.add_my_copy"),
                        icon=ft.Icons.ADD,
                        on_click=self._add,
                        expand=False,
                    ),
                ],
                spacing=6,
                tight=True,
            )

        item = self._item
        values = [
            (
                _("collections.condition"),
                (item.get("condition_type") or {}).get("name") or "-",
            ),
            (
                _("collections.quantity"),
                str(item.get("quantity") or "-"),
            ),
            (
                _("collections.paid"),
                fmt_currency(item.get("price_paid"), self._lang),
            ),
            (
                _("collections.acquired"),
                fmt_date(item.get("acquisition_date") or "", self._lang),
            ),
            (
                _("collections.location"),
                (item.get("location") or {}).get("name") or "-",
            ),
            (_("collections.note"), item.get("note") or "-"),
        ]

        return ft.Column(
            controls=[
                self.__caption(),
                *[
                    ft.Row(
                        controls=[
                            self.__cell(key, value)
                            for key, value in values[start:start + self.CELLS_PER_ROW]
                        ],
                        spacing=12,
                    )
                    for start in range(0, len(values), self.CELLS_PER_ROW)
                ],
            ],
            spacing=8,
            tight=True,
        )

    @staticmethod
    def __cell(key: str, value: str) -> ft.Column:
        """One label and its value, in the copy grid."""
        return ft.Column(
            controls=[
                ft.Text(key, size=FONT_SIZE_XS, color=GREY_700),
                ft.Text(
                    value,
                    size=FONT_SIZE_DEFAULT,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=0,
            tight=True,
            expand=True,
        )

    def __caption(self) -> ft.Row:
        """`YOUR COPY` and its two actions: the pencil, then the bin.

        Icons with a tooltip, grey until hovered, as the admin's header draws its
        own actions; a copy that is not there has nothing to delete.
        """
        actions: list[ft.Control] = [
            ActionIcon(
                icon=ft.Icons.EDIT,
                tooltip=_("collections.edit"),
                hover_color=ft.Colors.ORANGE_700,
                on_click=self._start_edit,
            )
        ]
        if self._item is not None:
            actions.append(
                ActionIcon(
                    icon=ft.Icons.DELETE,
                    tooltip=_("collections.remove"),
                    hover_color=ft.Colors.RED_700,
                    on_click=self._confirm_remove,
                )
            )

        return ft.Row(
            controls=[
                ft.Text(
                    _("collections.your_copy").upper(),
                    size=FONT_SIZE_XS,
                    weight=ft.FontWeight.BOLD,
                    color=GREY_700,
                ),
                ft.Container(expand=True),
                *actions,
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def __copy_form(self) -> ft.Control:
        """The six fields, in the same three-column grid, and the actions."""
        self._condition = self.__condition_field()
        self._quantity = TextField(
            label=_("collections.quantity"),
            value=str(self._item.get("quantity") or "")
            if self._item and self._item.get("quantity") is not None
            else "",
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._paid = TextField(
            label=_("collections.paid"),
            value=self._item.get("price_paid") or "" if self._item else "",
            expand=True,
        )
        self._date = DatePickerField(
            page=self._page,
            label=_("collections.acquired"),
            value=self.__date_value(),
            expand=True,
        )
        self._location = self.__location_field()
        self._note = TextField(
            label=_("collections.note"),
            value=self._item.get("note") or "" if self._item else "",
            expand=True,
        )
        self._error: ft.Text = ft.Text(
            "", color=RED, size=FONT_SIZE_XS, visible=False
        )
        references_warning = (
            ft.Text(
                _("collections.references_failed"),
                size=FONT_SIZE_XS,
                color=RED,
            )
            if not self._condition_types or not self._locations
            else None
        )

        actions = [
            DefaultButton(
                text=_("collections.cancel"),
                on_click=self._cancel,
                expand=False,
            ),
            PrimaryButton(
                text=_("collections.save"),
                on_click=self._save,
                expand=False,
            ),
        ]

        return ft.Column(
            controls=[
                self.__caption(),
                ft.Row(
                    controls=[self._condition, self._quantity, self._paid],
                    spacing=12,
                ),
                ft.Row(
                    controls=[self._date, self._location, self._note],
                    spacing=12,
                ),
                *([references_warning] if references_warning is not None else []),
                self._error,
                ft.Row(
                    controls=actions,
                    spacing=8,
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=8,
            tight=True,
        )

    def __condition_field(self) -> Dropdown:
        """The condition select, with the values the API returned.

        The house dropdown, so it wears the same underline as the fields beside
        it. It is disabled when the API returned no conditions: a copy cannot be
        given a value that does not exist, and the card says so above the form.
        """
        current = (self._item or {}).get("condition_type") or {}
        return Dropdown(
            label=_("collections.condition"),
            expand=True,
            value=str(current["id"]) if current.get("id") else None,
            options=[
                ft.dropdown.Option(
                    key=str(condition["id"]), text=condition["name"]
                )
                for condition in self._condition_types
            ],
            disabled=not self._condition_types,
        )

    def __location_field(self) -> Dropdown:
        """The location select, with the values the API returned."""
        current = (self._item or {}).get("location") or {}
        return Dropdown(
            label=_("collections.location"),
            expand=True,
            value=str(current["id"]) if current.get("id") else None,
            options=[
                ft.dropdown.Option(key=str(location["id"]), text=location["name"])
                for location in self._locations
            ],
            disabled=not self._locations,
        )

    def __date_value(self) -> Optional[datetime.date]:
        """The copy's date as a `date`, or None."""
        raw = (self._item or {}).get("acquisition_date")
        if not raw:
            return None
        try:
            return datetime.date.fromisoformat(str(raw))
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start_edit(self, event: ft.ControlEvent) -> None:
        """Show the form with the current values."""
        self._editing = True
        self._render_copy()

    def _cancel(self, event: ft.ControlEvent) -> None:
        """Go back to the display without saving."""
        self._editing = False
        self._render_copy()

    async def _save(self, event: ft.ControlEvent) -> None:
        """Validate, send the six fields and paint what the API returned."""
        if self._on_save is None or self._item is None:
            return

        payload = self._payload()
        if payload is None:
            return

        saved = await self._on_save(self._stamp, int(self._item["id"]), payload)
        if saved is None:
            self.__show_error(_("collections.save_failed"))
            return
        self.set_item(saved)

    def _payload(self) -> Optional[dict]:
        """The six fields, or None when one of them is invalid."""
        quantity = (self._quantity.value or "").strip()
        price = (self._paid.value or "").strip()

        if quantity:
            try:
                value = int(quantity)
            except ValueError:
                self.__show_error(_("collections.invalid_quantity"))
                return None
            if value < 1:
                self.__show_error(_("collections.invalid_quantity"))
                return None

        if price:
            try:
                Decimal(price)
            except InvalidOperation:
                self.__show_error(_("collections.invalid_price"))
                return None

        selected_date = self._date.value
        return {
            "condition_type": int(self._condition.value)
            if self._condition.value
            else None,
            "quantity": int(quantity) if quantity else None,
            "price_paid": price or None,
            "acquisition_date": selected_date.isoformat()
            if selected_date
            else None,
            "location": int(self._location.value)
            if self._location.value
            else None,
            "note": (self._note.value or "").strip() or None,
        }

    async def _add(self, event: ft.ControlEvent) -> None:
        """Ask for a copy of a stamp the user does not own."""
        if self._on_add is None:
            return
        item = await self._on_add(self._stamp)
        if item is not None:
            self.set_item(item)

    def _confirm_remove(self, event: ft.ControlEvent) -> None:
        """Ask once before removing the copy."""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                _("collections.remove"), size=20, font_family="Roboto-Bold"
            ),
            content=ft.Text(
                _("collections.remove_confirm", name=self._stamp.get("name") or "")
            ),
            actions=[
                DefaultButton(
                    text=_("collections.cancel"), on_click=self.__close, expand=False
                ),
                AlertButton(
                    text=_("collections.remove"),
                    on_click=self.__remove,
                    expand=False,
                ),
            ],
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
        self._confirm_dialog = dialog

    def __close(self, event: ft.ControlEvent = None) -> None:
        """Close the confirmation without deleting."""
        if self._confirm_dialog is not None:
            self._confirm_dialog.open = False
        self._page.update()

    async def __remove(self, event: ft.ControlEvent) -> None:
        """Delete the copy and go back to `Add my copy`."""
        self.__close()
        if self._on_remove is None or self._item is None:
            return
        if await self._on_remove(int(self._item["id"])):
            self.set_item(None)
        else:
            self.__show_error(_("collections.delete_failed"))

    def __show_error(self, message: str) -> None:
        """Say what failed without leaving the form."""
        if hasattr(self, "_error"):
            self._error.value = message
            self._error.visible = True
        try:
            self._page.update()
        except RuntimeError:
            pass
