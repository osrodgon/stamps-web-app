"""
Default button component for secondary actions.

This module provides the DefaultButton component for secondary actions
in the UI. It uses SKY_BLUE color and is suitable for non-primary actions.
"""

import flet as ft
from typing import Any, Callable, Optional

from components.colors import SKY_BLUE
from components.constants import BUTTON_TEXT_SIZE, BUTTON_HEIGHT, BUTTON_BORDER_RADIUS


class DefaultButton(ft.Button):
    """A secondary action button component for Flet applications.

    This component represents a secondary action button (e.g., 'Cancel', 'Back').
    It features SKY_BLUE text color, rounded corners, and optional icon support.

    Attributes:
        (Inherited from ft.Button)
    """

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable[..., None]] = None,
        data: Optional[Any] = None,
        icon: Optional[str] = None,
        expand: bool = True,
    ) -> None:
        """Initializes a DefaultButton with the specified text and behavior.

        Args:
            text (str): The text to display on the button.
            on_click (callable, optional): Callback function triggered when
                the button is clicked. Receives the Flet click event.
                Defaults to None.
            data (any, optional): Arbitrary data to attach to the button,
                accessible via e.control.data in the click handler.
                Useful for passing context such as form field references.
                Defaults to None.
            icon (ft.Icon, optional): Icon to display on the button.
            expand (bool, optional): Whether button expands to fill available
                horizontal space. Defaults to True.
        """
        super().__init__()
        self.content = ft.Text(text, size=BUTTON_TEXT_SIZE)
        self.color = SKY_BLUE
        
        self.height = BUTTON_HEIGHT
        self.data = data
        self.on_click = on_click
        self.expand = expand
        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BUTTON_BORDER_RADIUS),
        )
        self.font_style = "Roboto"
        if icon:
            self.icon = icon
    
