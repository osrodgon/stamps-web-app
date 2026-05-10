import flet as ft
from components.colors import SKY_BLUE, SKY_BLUE_HOVER, SKY_BLUE_DISABLED


class PrimaryButton(ft.Button):
    """
    A primary action button component for Flet applications.

    This component represents the main call-to-action button (e.g., 'Sign In',
    'Submit', 'Save'). It features a solid background color that lightens on
    hover, white text, and a rounded border.

    The button expands to fill available horizontal space. Colors are sourced 
        from the centralized color module (SKY_BLUE, SKY_BLUE_HOVER).

    Attributes:
        (Inherited from ft.Button)
    """

    def __init__(self, text, on_click=None, data=None, icon=None, expand=True):
        """
        Initializes a PrimaryButton with the specified text and behavior.

        Args:
            text (str): The text to display on the button.
            on_click (callable, optional): Callback function triggered when
                the button is clicked. Receives the Flet click event.
                Defaults to None.
            data (any, optional): Arbitrary data to attach to the button,
                accessible via e.control.data in the click handler.
                Useful for passing context such as form field references.
                Defaults to None.
        """
        super().__init__()
        self.content = ft.Text(text, size=14)
        self.color = ft.Colors.WHITE
        self.bgcolor = {
            ft.ControlState.DEFAULT: SKY_BLUE,
            ft.ControlState.DISABLED: SKY_BLUE_DISABLED
        }
        self.height = 40
        self.data = data
        self.on_click = on_click
        self.expand = expand
        self.on_hover = self._on_hover
        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4),
        )
        self.font_style = "Roboto"
        if icon:
            self.icon = icon
    
    def _on_hover(self, e):
        """
        Handles the hover state change for the button.

        Changes the button's background color based on whether the mouse
        is currently hovering over the button. Lightens the color on hover
        and restores the default color when not hovering.

        Args:
            e (ft.HoverEvent): The hover event containing the hover state
                in e.data (string 'true' when hovered, 'false' otherwise).
        """
        if e.data:  # Hovered
            self.bgcolor = {
                ft.ControlState.DEFAULT: SKY_BLUE_HOVER,
                ft.ControlState.DISABLED: SKY_BLUE_DISABLED
            }
        else:  # Not hovered
            self.bgcolor = {
                ft.ControlState.DEFAULT: SKY_BLUE,
                ft.ControlState.DISABLED: SKY_BLUE_DISABLED
            }
        self.update()
    