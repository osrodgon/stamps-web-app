"""
Styled date picker field with FieldStyle preset support.

Extends the custom ``TextField`` with a native Flet ``DatePicker`` dialog,
matching the same visual style. Clicking the field opens the picker;
selecting a date updates the display and fires the ``on_change`` callback.
"""

import datetime
from typing import Any, Callable, Optional

import flet as ft

from components.form.text_field import DEFAULT, FieldStyle, TextField
from components.table.column_def import fmt_date
from core.translations import get_language
from core.utils import _read_client_timezone, get_local_today, to_local_date
from settings import DEFAULT_TIMEZONE




class DatePickerField(TextField):
    """A text-field-styled date picker with native DatePicker dialog.

    Presents a read-only text field that opens a DatePicker on click.
    The selected date is displayed formatted via ``fmt_date`` using the
    current application language.  Supports ``FieldStyle`` presets for
    consistent visual styling with other form controls.

    Attributes:
        value: The currently selected date, or None.
    """

    def __init__(
        self,
        page: ft.Page,
        label: str,
        value: Optional[datetime.date] = None,
        on_change: Optional[Callable[[datetime.date], None]] = None,
        field_style: FieldStyle = DEFAULT,
        first_date: Optional[datetime.date] = None,
        last_date: Optional[datetime.date] = None,
        expand: Optional[bool] = None,
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initializes the DatePickerField.

        Args:
            page: The Flet page (used to append DatePicker to overlay).
            label: Label text for the display field.
            value: Initially selected date, or None.
            on_change: Called with the selected ``datetime.date`` when it
                changes.
            field_style: ``FieldStyle`` preset for visual styling.
            first_date: Earliest selectable date (default 1800-01-01).
            last_date: Latest selectable date (default today).
            expand: Whether the field expands to fill available width.
                Overrides field_style.
            width: Fixed width of the field. Overrides expand when set.
            **kwargs: Additional properties forwarded to ``TextField``.
        """
        self._selected_date: Optional[datetime.date] = value
        self._on_change_callback: Optional[Callable[[datetime.date], None]] = on_change

        self._page: ft.Page = page

        self._picker: ft.DatePicker = ft.DatePicker(
            on_change=self._on_picker_change,
            first_date=first_date or datetime.date(1800, 1, 1),
            last_date=last_date or get_local_today() + datetime.timedelta(days=365),
        )
        page.overlay.append(self._picker)

        display_text: str = fmt_date(value.isoformat(), get_language()) if value else ""

        # Don't pass value to super().__init__ — ft.TextField.__init__ would
        # trigger our overridden value setter with a string.  Set it after via
        # the parent Prop descriptor directly.
        super().__init__(
            label=label,
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            on_click=self._on_field_click,
            field_style=field_style,
            expand=expand,
            width=width,
            **kwargs,
        )

        if display_text:
            ft.TextField.__dict__["value"].__set__(self, display_text)

    @property
    def value(self) -> Optional[datetime.date]:
        """The currently selected date, or None."""
        return self._selected_date

    @value.setter
    def value(self, new_value: Optional[datetime.date]) -> None:
        """Set the selected date and update the display text.

        Args:
            new_value: The new date, or None to clear.
        """
        # Ignore string values set internally by ft.TextField.__init__
        if isinstance(new_value, str):
            return
        self._selected_date = new_value
        text: str = fmt_date(new_value.isoformat(), get_language()) if new_value else ""
        ft.TextField.__dict__["value"].__set__(self, text)

    def set_today(self) -> None:
        """Set the value to today's date and fire the ``on_change`` callback."""
        today: datetime.date = get_local_today()
        self.value = today
        if self._on_change_callback:
            self._on_change_callback(today)

    def _on_field_click(self, e: ft.ControlEvent) -> None:
        """Open the DatePicker dialog.

        Args:
            e: The click event from the text field.
        """
        self._page.show_dialog(self._picker)

    async def _on_picker_change(self, e: ft.ControlEvent) -> None:
        """Handle date selection from the DatePicker dialog.

        Args:
            e: The DatePicker change event with ``e.control.value``.
        """
        if not e.control or not e.control.value:
            return
        raw = e.control.value
        if isinstance(raw, datetime.datetime):
            tz = await _read_client_timezone() or DEFAULT_TIMEZONE
            self._selected_date = to_local_date(raw, tz)
        else:
            self._selected_date = raw
        text: str = fmt_date(self._selected_date.isoformat(), get_language())
        ft.TextField.__dict__["value"].__set__(self, text)
        self._page.update()
        if self._on_change_callback:
            self._on_change_callback(self._selected_date)
