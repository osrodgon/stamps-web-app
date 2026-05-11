import flet as ft

from components.colors import SKY_BLUE

class DefaultButton(ft.Button):
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
        self.color = SKY_BLUE
        
        self.height = 40
        self.data = data
        self.on_click = on_click
        self.expand = expand
        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4),
        )
        self.font_style = "Roboto"
        if icon:
            self.icon = icon
    
