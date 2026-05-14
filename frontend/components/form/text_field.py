"""
Custom styled TextField component with preset styling profiles.

Provides a reusable text field built on ft.TextField with support for
a FieldStyle dataclass that groups common styling attributes (border,
colors, padding, label style). Two presets are available:

  - DEFAULT:   Underline border, blue accents, expands to fill width.
               Used in login/signup forms.
  - APP_HEADER: Underline border, grey accents, no expand, white text.
               Used in the page header filter.
"""

from dataclasses import dataclass

import flet as ft
from typing import Any, Callable, Optional

from components.colors import BLUE_GREY_100, BLUE_700


@dataclass
class FieldStyle:
    """A set of styling parameters for a TextField.

    All values default to None, meaning "use the ft.TextField default".
    Non-None values are applied during TextField initialization.
    FieldStyle values are overridable by passing the same attribute
    as an explicit keyword argument to the TextField constructor.

    Attributes:
        border: Border style (UNDERLINE, OUTLINE, NONE).
        expand: Whether the field expands to fill available width.
        border_color: Border color hex when not focused.
        focused_border_color: Border color hex when focused.
        text_size: Font size for the input text.
        color: Text color of the entered value.
        cursor_color: Color of the text cursor.
        border_width: Border thickness in pixels.
        focused_border_width: Border thickness when focused.
        content_padding: Internal padding around the input area.
        label_style: TextStyle for the floating label.
    """

    border: ft.InputBorder = ft.InputBorder.UNDERLINE
    expand: bool = True
    border_color: str = BLUE_GREY_100
    focused_border_color: str = BLUE_700
    text_size: int = 14
    color: str | None = None
    cursor_color: str | None = None
    border_width: int | None = None
    focused_border_width: int | None = None
    content_padding: ft.Padding | None = None
    label_style: ft.TextStyle | None = None


# Standard form fields — underline border, blue accents, auto-expands
DEFAULT: FieldStyle = FieldStyle()

# Page header filter — underline border, grey accents, fixed width
APP_HEADER: FieldStyle = FieldStyle(
    expand=False,
    border_color=ft.Colors.GREY_500,
    focused_border_color=ft.Colors.GREY_500,
    text_size=14,
    color=ft.Colors.WHITE,
    cursor_color=ft.Colors.GREY_500,
    border_width=1,
    focused_border_width=2,
    content_padding=ft.Padding(bottom=0, top=0),
    label_style=ft.TextStyle(color=ft.Colors.GREY_500, font_family="Roboto"),
)


class TextField(ft.TextField):
    """A customized text input field component for Flet applications.

    Extends ft.TextField with a FieldStyle preset system for easy
    styling. Supports password fields with reveal toggle, custom
    border colors, and full ft.TextField compatibility via **kwargs.

    Styling resolution order:
      1. field_style preset provides base values
      2. Explicit keyword arguments override field_style
      3. **kwargs catch any remaining ft.TextField properties
         (color, cursor_color, border_width, tooltip, etc.)

    Attributes:
        is_focused: Whether the field currently has keyboard focus.
    """

    is_focused: bool = False

    def __init__(
        self,
        label: str,
        password: bool = False,
        can_reveal_password: bool = False,
        border_color: Optional[str] = None,
        focused_border_color: Optional[str] = None,
        width: Optional[int] = None,
        on_click: Optional[Callable[..., None]] = None,
        on_change: Optional[Callable[..., None]] = None,
        expand: Optional[bool] = None,
        border: Optional[ft.InputBorder] = None,
        text_size: Optional[int] = None,
        label_style: Optional[ft.TextStyle] = None,
        field_style: FieldStyle = DEFAULT,
        **kwargs: Any,
    ) -> None:
        """Initializes a TextField with the specified label and behavior.

        Styling is resolved from field_style first, then overridden
        by any explicit argument.  This means:
          TextField(label="X")                          → uses DEFAULT
          TextField(label="X", field_style=APP_HEADER)  → uses APP_HEADER
          TextField(label="X", border_color=RED)        → RED overrides DEFAULT

        Args:
            label: The label text displayed above or inside the field.
            password: If True, the field masks input as a password field.
            can_reveal_password: If True and password is True, displays a
                toggle icon to reveal/hide the password.
            border_color: Border color when not focused. Overrides field_style.
            focused_border_color: Border color when focused. Overrides field_style.
            width: Fixed width of the field. None = auto/expand.
            on_click: Callback for click events.
            on_change: Callback for text change events.
            expand: Whether the field expands to fill available width.
                Overrides field_style.
            border: Border style (UNDERLINE, OUTLINE, NONE).
                Overrides field_style.
            text_size: Font size of the input text. Overrides field_style.
            label_style: TextStyle for the label. Overrides field_style.
            field_style: A FieldStyle preset providing default styling.
                Overridable by any of the explicit params above.
            **kwargs: Additional ft.TextField properties (color, cursor_color,
                border_width, focused_border_width, content_padding, tooltip,
                hint_text, suffix_icon, prefix_icon, etc.).
        """
        super().__init__(**kwargs)
        self.label = label
        self.password = password
        self.can_reveal_password = can_reveal_password
        self.font_family = "Roboto"

        # Apply field_style defaults, then let explicit params override
        self.border_color = border_color if border_color is not None else field_style.border_color
        self.focused_border_color = focused_border_color if focused_border_color is not None else field_style.focused_border_color
        self.text_size = text_size if text_size is not None else field_style.text_size
        self.expand = expand if expand is not None else field_style.expand
        self.border = border if border is not None else field_style.border

        # Non-conflicting field_style properties (no explicit param equivalent)
        if field_style.color:
            self.color = field_style.color
        if field_style.cursor_color:
            self.cursor_color = field_style.cursor_color
        if field_style.border_width is not None:
            self.border_width = field_style.border_width
        if field_style.focused_border_width is not None:
            self.focused_border_width = field_style.focused_border_width
        if field_style.content_padding is not None:
            self.content_padding = field_style.content_padding

        self.label_style = label_style or field_style.label_style
        self.on_click = on_click
        self.on_change = on_change
        self.width = width
