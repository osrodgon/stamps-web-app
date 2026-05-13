import flet as ft
from typing import Any, Callable, Optional

from components.colors import BLUE_GREY_100, BLUE_700


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
        border_color: str = BLUE_GREY_100,
        focused_border_color: str = BLUE_700,
        width: Optional[int] = None,
        on_click: Optional[Callable[..., None]] = None,
        on_change: Optional[Callable[..., None]] = None,
        expand: bool = True,
        border: ft.InputBorder = ft.InputBorder.UNDERLINE,
        text_size: int = 14,
        label_style: Optional[ft.TextStyle] = None,
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
        self.border_color = border_color
        self.focused_border_color = focused_border_color
        self.text_size = text_size
        self.expand = expand
        self.border = border
        self.font_family = "Roboto"
        self.on_click = on_click
        self.on_change = on_change
        self.width = width
        if label_style:
            self.label_style = label_style
