from typing import Optional

import flet as ft

from components.colors import SKY_BLUE, SKY_BLUE_HOVER
from components.constants import FONT_SIZE_DEFAULT


class LinkButton(ft.TextButton):
    """
    A link-styled button component for Flet applications.

    This component renders a button that visually resembles a hyperlink
    (underlined text) rather than a standard button. It is typically used
    for secondary actions such as navigation links (e.g., 'Sign Up',
    'Forgot Password').

    The button changes color on hover and uses a transparent overlay to
    maintain the clean link appearance. Colors are sourced from the
    centralized color module (SKY_BLUE, SKY_BLUE_HOVER).

    Attributes:
        (Inherited from ft.TextButton)
    """

    def __init__(
        self,
        text,
        on_click=None,
        data=None,
        size=FONT_SIZE_DEFAULT,
        underline: bool = True,
        padding: Optional[ft.Padding] = None,
    ):
        """
        Initializes a LinkButton with the specified text and behavior.

        Args:
            text (str): The text to display on the link button.
            on_click (callable, optional): Callback function triggered when
                the button is clicked. Receives the Flet click event.
                Defaults to None.
            data (any, optional): Arbitrary data to attach to the button,
                accessible via e.control.data in the click handler.
                Useful for passing context or identifiers. Defaults to None.
            size (int, optional): The font size for the button text.
                Defaults to 14.
            underline (bool, optional): Whether the label is underlined. A
                breadcrumb turns it off: a line under every crumb reads as an
                accident, not as a link. Defaults to True.
            padding (ft.Padding, optional): The button's own padding. A breadcrumb
                passes `Padding.all(0)` so the gaps around its separators are the
                row's and not the button's. Defaults to the Material one.
        """
        style = ft.ButtonStyle(
            color={
                "hovered": SKY_BLUE_HOVER,
                "default": SKY_BLUE
            },
            overlay_color=ft.Colors.TRANSPARENT,
            text_style=ft.TextStyle(
                decoration=(
                    ft.TextDecoration.UNDERLINE
                    if underline
                    else ft.TextDecoration.NONE
                )
            ),
        )
        if padding is not None:
            style.padding = padding

        super().__init__(
            content=ft.Text(text, size=size, font_family="Roboto"),
            on_click=on_click,
            data=data,
            style=style,
        )
