import flet as ft
from components.colors import SLATE_GREY, SLATE_GREY_HOVER


class TextButton(ft.TextButton):
    """
    A secondary text button component for Flet applications.

    This component renders a subtle, text-based button without the prominent
    styling of a primary button. It is used for secondary actions such as
    language selectors, contextual links, or less prominent UI interactions.

        The button uses a slate grey color scheme (SLATE_GREY) that lightens
    on hover, with a transparent overlay to maintain a clean appearance.
    Colors are sourced from the centralized color module.

    Attributes:
        (Inherited from ft.TextButton)
    """

    def __init__(self, text, on_click=None, data=None, size=16, font_family="Roboto"):
        """
        Initializes a TextButton with the specified text and styling.

        Args:
            text (str): The text to display on the button.
            on_click (callable, optional): Callback function triggered when
                the button is clicked. Receives the Flet click event.
                Defaults to None.
            data (any, optional): Arbitrary data to attach to the button,
                accessible via e.control.data in the click handler.
                Useful for passing context or identifiers. Defaults to None.
            size (int, optional): The font size for the button text.
                Defaults to 16.
            weight (ft.FontWeight, optional): The font weight for the button text.
                Defaults to ft.FontWeight.NORMAL.
        """
        super().__init__()
        self.content = ft.Text(text, size=size, font_family=font_family)
        self.style = ft.ButtonStyle(
            color={
                "default": SLATE_GREY,
                "hovered": SLATE_GREY_HOVER
            },
            overlay_color=ft.Colors.TRANSPARENT
        )
        self.on_click = on_click
        self.data = data