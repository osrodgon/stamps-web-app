"""Editable dropdown wrapping ft.Dropdown with selected_id tracking."""

from typing import Callable, Optional

import flet as ft

from components.constants import FONT_SIZE_DEFAULT
from components.colors import GREY_700


class AutoCompleteField(ft.Container):
    """Editable Dropdown with filter/search, tracks selected_id.

    Attributes:
        selected_id: The ID of the selected option, or ``None`` for free text.
        text: The current input text.
    """

    def __init__(
        self,
        items: list[dict],
        expand: bool = True,
        width: Optional[int] = None,
        suggestions_max_height: int = 200,
        margin: Optional[ft.Margin] = None,
        hint_text: Optional[str] = None,
        on_select: Optional[Callable[[int], None]] = None,
    ) -> None:
        self._items: list[dict] = items
        self._id_to_name: dict[str, str] = {
            str(item["id"]): item["name"] for item in items
        }
        self._selected_id: Optional[int] = None
        self._on_select_callback: Optional[Callable[[int], None]] = on_select

        self._dropdown: ft.Dropdown = ft.Dropdown(
            height=20,
            text_size=FONT_SIZE_DEFAULT,
            #text_style=ft.TextStyle(bgcolor="#FFF8E1"),
            dense=True,
            content_padding=ft.Padding(0, 0, 0, 0),
            border=ft.InputBorder.NONE,
            filled=False,
            editable=True,
            enable_filter=True,
            enable_search=True,
            options=[
                ft.dropdown.Option(key=str(item["id"]), text=item["name"])
                for item in items
            ],
            on_text_change=self._on_text_change,
            on_select=self._on_select,
            menu_height=suggestions_max_height,
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.BOTTOM_LEFT,
            ),
            hint_text=hint_text,
            hint_style=ft.TextStyle(color=GREY_700, italic=True, size=FONT_SIZE_DEFAULT)
        )

        super().__init__(
            content=self._dropdown,
            expand=expand,
            width=width,
            padding=0,
            margin=margin,
        )

    @property
    def selected_id(self) -> Optional[int]:
        return self._selected_id

    @property
    def text(self) -> str:
        return self._dropdown.text or ""

    def set_text(self, name: str) -> None:
        """Set the field value and resolve ``selected_id``."""
        for item in self._items:
            if item["name"] == name:
                self._dropdown.value = str(item["id"])
                self._selected_id = item["id"]
                return
        self._dropdown.value = name
        self._selected_id = None

    def _on_select(self, e: ft.ControlEvent) -> None:
        """Update selected_id when an option is selected."""
        if e.data:
            self._selected_id = int(e.data)
            if self._on_select_callback:
                self._on_select_callback(self._selected_id)
        else:
            self._selected_id = None
            
    def _on_text_change(self, e) -> None:
        for item in self._items:
            if item["name"] == e.data:
                self._dropdown.value = str(item["id"])
                self._selected_id = item["id"]
                if self._on_select_callback:
                    self._on_select_callback(self._selected_id)
                return
        self._dropdown.value = e.data
        self._selected_id = None

