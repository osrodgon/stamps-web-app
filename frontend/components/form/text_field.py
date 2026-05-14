from dataclasses import dataclass

import flet as ft
from typing import Any, Callable, Optional

from components.colors import BLUE_GREY_100, BLUE_700

@dataclass
class FieldStyle:
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


DEFAULT = FieldStyle()
APP_HEADER = FieldStyle(
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
    """
    A customized text input field component for Flet applications.

    This component extends the standard Flet TextField with predefined
    styling: underlined border, expanded width, and custom border colors
    for default and focused states. It supports both standard text input
    and password fields with optional reveal toggle.

    Colors are sourced from the centralized color module
    (BLUE_GREY_100, BLUE_700).

    Attributes:
        (Inherited from ft.TextField)
    """
    
    is_focused: bool = False

    def __init__(
        self,
        label: str,
        password: bool = False,
        can_reveal_password: bool = False,
        border_color: Optional[str] = None,            # was: = BLUE_GREY_100
        focused_border_color: Optional[str] = None,      # was: = BLUE_700
        width: Optional[int] = None,
        on_click: Optional[Callable[..., None]] = None,
        on_change: Optional[Callable[..., None]] = None,
        expand: Optional[bool] = None,                   # was: = True
        border: Optional[ft.InputBorder] = None,          # was: = UNDERLINE
        text_size: Optional[int] = None,                 # was: = 14
        label_style: Optional[ft.TextStyle] = None,
        field_style: FieldStyle = DEFAULT,
        **kwargs: Any,
    ) -> None:
        """
        Initializes a TextField with the specified label and behavior.

        Args:
            label: The label text displayed above or inside the field.
            password: If True, the field masks input as a password field.
            can_reveal_password: If True and password is True, displays a
                toggle icon to reveal/hide the password.
            border_color: Border color when not focused.
            focused_border_color: Border color when focused.
            width: Fixed width of the field. None = auto/expand.
            on_click: Callback for click events.
            expand: Whether the field expands to fill available space.
            border: Border style (UNDERLINE, OUTLINE, NONE, etc.).
            text_size: Font size of the input text.
            label_style: TextStyle for the label (color, size, font, etc.).
            **kwargs: Additional ft.TextField properties (color, cursor_color,
                border_width, content_padding, tooltip, etc.).
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
