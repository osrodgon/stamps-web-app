"""
Table pagination component for the issue table.

Provides page size selection, range display, and navigation controls.
"""

import asyncio
from typing import Callable, Optional

import flet as ft

from components.colors import BG_LIGHT, ICON_GREY, ROW_BORDER
from components.table.column_def import fmt_number
from core.translations import _, get_language
from components.constants import FONT_SIZE_DEFAULT, ICON_SIZE_SMALL, STANDARD_PADDING

class TablePagination(ft.Container):
    """Footer pagination controls.

    Displays a page-size dropdown, current range text (e.g. "1-15 of 65"),
    and four navigation buttons: first, previous, next, last.
    """

    def __init__(
        self,
        page: int = 1,
        page_size: int = 15,
        total: int = 0,
        on_page_change: Optional[Callable[[int], None]] = None,
        on_page_size_change: Optional[Callable[[int], None]] = None,
        font_size: int = FONT_SIZE_DEFAULT,
        font_family: str = "Roboto-Bold",
        page_size_options: Optional[list[int]] = None,
        label: str = "",
    ) -> None:
        """Initialize pagination controls with current state and callbacks.

        Builds a bottom-right-aligned row containing:
          - "Rows per page:" label + dropdown
          - Range text (e.g. "1-15 of 65")
          - Four nav buttons: first, prev, next, last

        Args:
            page: Current page number (1-indexed).
            page_size: Number of items per page.
            total: Total number of items across all pages.
            on_page_change: Called when the user navigates to a different page.
            on_page_size_change: Called when the user selects a new page size.
            font_size: Font size for text elements.
            font_family: Font family for text elements.
            page_size_options: The sizes the dropdown offers. Defaults to the list
                this component has always shown.
            label: What the dropdown is for, translated. Defaults to the existing
                `pagination.rows_per_page` key.
        """
        super().__init__()
        self._page: int = page
        self._page_size: int = page_size
        self._total: int = total
        self._on_page_change: Optional[Callable[[int], None]] = on_page_change
        self._on_page_size_change: Optional[Callable[[int], None]] = on_page_size_change
        self._syncing: bool = False
        self._page_size_options: list[int] = page_size_options or [
            1,
            10,
            15,
            20,
            50,
            100,
        ]
        self._label: str = label or _("pagination.rows_per_page")

        self._range_text: ft.Text = ft.Text(
            self._format_range(), 
            size=font_size,
            font_family=font_family
        )
        self._dropdown: ft.Dropdown = ft.Dropdown(
            value=str(page_size),
            options=[
                ft.dropdown.Option(str(size)) for size in self._page_size_options
            ],
            width=50,
            height=None,
            text_size=font_size,
            text_style=ft.TextStyle(font_family=font_family),
            border=ft.InputBorder.NONE,
        )
        self._dropdown.on_text_change = self._on_dropdown_change
        self._first_btn: ft.IconButton = self._nav_button(
            ft.Icons.FIRST_PAGE,
            self._go_first,
        )
        self._prev_btn: ft.IconButton = self._nav_button(
            ft.Icons.NAVIGATE_BEFORE,
            self._go_prev,
        )
        self._next_btn: ft.IconButton = self._nav_button(
            ft.Icons.NAVIGATE_NEXT,
            self._go_next,
        )
        self._last_btn: ft.IconButton = self._nav_button(
            ft.Icons.LAST_PAGE,
            self._go_last,
        )

        self.alignment = ft.Alignment.CENTER_RIGHT
        self.padding = ft.Padding.symmetric(horizontal=STANDARD_PADDING, vertical=4)
        self.border = ft.Border.only(top=ft.BorderSide(1, ROW_BORDER))
        self.content = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"{self._label}:",
                            size=font_size,
                            font_family=font_family,
                        ),
                        self._dropdown,
                    ],
                    spacing=4,
                ),
                self._range_text,
                ft.Row(
                    controls=[
                        self._first_btn,
                        self._prev_btn,
                        self._next_btn,
                        self._last_btn,
                    ],
                    spacing=0,
                ),
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.bgcolor=BG_LIGHT

    def _nav_button(self, icon: str, on_click: Callable) -> ft.IconButton:
        """Create a pagination navigation icon button."""
        return ft.IconButton(
            icon=icon,
            icon_size=ICON_SIZE_SMALL,
            on_click=on_click,
            icon_color=ICON_GREY,
        )

    def _format_range(self) -> str:
        """Format the current range string, e.g. '1-15 of 65'."""
        if self._total == 0:
            return "0 of 0"
        start: int = (self._page - 1) * self._page_size + 1
        end: int = min(self._page * self._page_size, self._total)
        lang: str = get_language()
        return f"{fmt_number(start, lang)}-{fmt_number(end, lang)} {_('common.of')} {fmt_number(self._total, lang)}"

    def _total_pages(self) -> int:
        """Calculate total pages."""
        if self._total == 0:
            return 0
        return (self._total - 1) // self._page_size + 1

    def _update_nav_buttons(self) -> None:
        """Enable or disable navigation buttons based on current page."""
        total: int = self._total_pages()
        self._set_button_state(self._first_btn, self._page <= 1)
        self._set_button_state(self._prev_btn, self._page <= 1)
        self._set_button_state(self._next_btn, self._page >= total)
        self._set_button_state(self._last_btn, self._page >= total)

    def _set_button_state(self, btn: ft.IconButton, disabled: bool) -> None:
        """Set a navigation button's enabled state and matching icon color."""
        btn.disabled = disabled
        btn.icon_color = ROW_BORDER if disabled else ICON_GREY

    def _on_dropdown_change(self, e: ft.ControlEvent) -> None:
        """Handle page size dropdown change."""
        if self._syncing:
            # A programmatic value from `update_state`, not the user: firing the
            # callback would ask for the page again and loop.
            return

        value: str = e.control.value
        new_size: int = 0 if value == _("pagination.all_rows") else int(value)
        self._page_size = new_size
        self._page = 1
        self._range_text.value = self._format_range()
        self._update_nav_buttons()
        self.update()
        self._dropdown.width = max(70, len(value) * 17+ 30)

        self._dispatch(self._on_page_size_change, new_size)

    def _go_first(self, e: ft.ControlEvent) -> None:
        """Navigate to the first page."""
        self._page = 1
        self._range_text.value = self._format_range()
        self._update_nav_buttons()
        self.update()
        self._dispatch(self._on_page_change, self._page)

    def _go_prev(self, e: ft.ControlEvent) -> None:
        """Navigate to the previous page."""
        if self._page > 1:
            self._page -= 1
            self._range_text.value = self._format_range()
            self._update_nav_buttons()
            self.update()
            self._dispatch(self._on_page_change, self._page)

    def _go_next(self, e: ft.ControlEvent) -> None:
        """Navigate to the next page."""
        if self._page < self._total_pages():
            self._page += 1
            self._range_text.value = self._format_range()
            self._update_nav_buttons()
            self.update()
            self._dispatch(self._on_page_change, self._page)

    def _go_last(self, e: ft.ControlEvent) -> None:
        """Navigate to the last page."""
        self._page = self._total_pages()
        self._range_text.value = self._format_range()
        self._update_nav_buttons()
        self.update()
        self._dispatch(self._on_page_change, self._page)

    def update_state(
        self,
        page: int,
        page_size: int,
        total: int,
    ) -> None:
        """Update pagination state from parent (e.g., after API call)."""
        self._page = page
        self._page_size = page_size
        self._total = total
        self._range_text.value = self._format_range()
        self._syncing = True
        self._dropdown.value = str(page_size)
        self._syncing = False
        self._update_nav_buttons()
        self.update()

    @staticmethod
    def _dispatch(callback: Optional[Callable], *args) -> None:
        """Call a callback; when it is a coroutine, schedule it.

        The paginator is used by pages whose handlers are `async` (the collections
        screens) and by the admin's table, whose handlers are plain functions.
        Calling an async one directly returned a coroutine that was never awaited,
        so the page never changed.
        """
        if callback is None:
            return
        result = callback(*args)
        if asyncio.iscoroutine(result):
            asyncio.create_task(result)
