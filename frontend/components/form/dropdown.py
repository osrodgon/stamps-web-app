"""
Custom styled Dropdown component with preset styling profiles.

Provides a reusable dropdown built on ft.Dropdown that shares the same
FieldStyle dataclass from text_field.py for consistent visual styling
across form controls. Supports the same two presets:

  - DEFAULT:   Underline border, blue accents, expands to fill width.
  - APP_HEADER: Underline border, grey accents, no expand, white text.
"""

from typing import Any, Callable, Optional

import flet as ft

from components.form.text_field import APP_HEADER, DEFAULT, FieldStyle


class Dropdown(ft.Dropdown):
    """A styled dropdown selector matching the visual style of TextField.

    Extends ft.Dropdown with a FieldStyle preset system that mirrors
    the TextField component exactly. Styling resolution order:
      1. field_style preset provides base values
      2. Explicit keyword arguments override field_style
      3. **kwargs catch any remaining ft.Dropdown properties

    Attributes:
        value: The currently selected option key.
        options: List of ft.dropdown.Option items.
    """

    def __init__(
        self,
        label: str,
        options: list[ft.dropdown.Option],
        value: Optional[str] = None,
        width: Optional[int] = None,
        on_change: Optional[Callable[..., None]] = None,
        on_focus: Optional[Callable[..., None]] = None,
        expand: Optional[bool] = None,
        border: Optional[ft.InputBorder] = None,
        text_size: Optional[int] = None,
        label_style: Optional[ft.TextStyle] = None,
        border_color: Optional[str] = None,
        focused_border_color: Optional[str] = None,
        text_align: Optional[ft.TextAlign] = None,
        filled: Optional[bool] = None,
        fill_color: Optional[str] = None,
        field_style: FieldStyle = DEFAULT,
        **kwargs: Any,
    ) -> None:
        """Initializes a Dropdown with consistent FieldStyle-based styling.

        Args:
            label: The label text displayed above or inside the field.
            options: List of ft.dropdown.Option items.
            value: The initially selected option key.
            width: Fixed width of the dropdown. None = auto/expand.
            on_change: Callback when selection changes. Set as attribute
                after construction (Flet 0.84.0 compatibility).
            on_focus: Callback when the field gains focus.
            expand: Whether the field expands to fill available width.
                Overrides field_style.
            border: Border style (UNDERLINE, OUTLINE, NONE).
                Overrides field_style.
            text_size: Font size of the input text. Overrides field_style.
            label_style: TextStyle for the label. Overrides field_style.
            border_color: Border color when not focused. Overrides field_style.
            focused_border_color: Border color when focused.
                Overrides field_style.
            text_align: Text alignment (e.g. RIGHT for numeric values).
            filled: If True, uses filled background instead of underline.
            fill_color: Background color when filled=True.
            field_style: A FieldStyle preset providing default styling.
                Overridable by any of the explicit params above.
            **kwargs: Additional ft.Dropdown properties (hint_text,
                hint_style, helper_text, helper_style, error_text, etc.).
        """
        super().__init__(**kwargs)
        self.label = label
        self.options = options
        self.value = value
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
        if field_style.border_width is not None:
            self.border_width = field_style.border_width
        if field_style.focused_border_width is not None:
            self.focused_border_width = field_style.focused_border_width
        if field_style.content_padding is not None:
            self.content_padding = field_style.content_padding

        self.label_style = label_style or field_style.label_style

        if text_align is not None:
            self.text_align = text_align
        if filled is not None:
            self.filled = filled
        if fill_color is not None:
            self.fill_color = fill_color

        self.on_focus = on_focus
        self.width = width

        # on_change must be set after super().__init__ (Flet 0.84.0)
        if on_change is not None:
            self.on_change = on_change
