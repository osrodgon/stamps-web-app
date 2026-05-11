import flet as ft
from components.colors import lighten_color, DARK_BLUE_GREY

class IconButton(ft.Container):
    """
    A circular icon button component.
    
    Displays an icon in a circular container with optional click handling.
    Commonly used in headers, toolbars, or as action buttons.
    
    Attributes:
        icon (ft.Icon): The icon displayed in the button.
    """
    
    def __init__(self, icon: str, bgcolor: str, size: int = 40, on_click=None, data=None):
        """
        Initialize a circular IconButton.
        
        Args:
            icon (str): The icon name from ft.Icons (e.g., "add", "delete").
            bgcolor (str): Background color of the button (hex or ft.Colors).
            size (int, optional): Diameter of the circular button. Default: 40.
            on_click (callable, optional): Callback function triggered on click.
            data (any, optional): Arbitrary data attached to the button.
        """
        super().__init__()
        self.width = size
        self.height = size
        self.bgcolor = bgcolor
        self.border_radius = size // 2  # Makes it circular
        self.content = ft.Icon(
            icon=icon,
            size=size * 0.6,  # Icon is 60% of button size
            color=ft.Colors.WHITE,
        )
        self.on_click = on_click
        self.data = data
        self.alignment = ft.Alignment.CENTER
        self.on_hover = self._on_hover
        
    def _on_hover(self, e: ft.HoverEvent) -> None:
        """
        Handle hover state changes for the button.

        Lightens the button's background color when the mouse enters the
        button area and restores the original color when the mouse leaves.

        Args:
            e (ft.HoverEvent): The hover event containing the hover state
                in e.data ('true' when hovered, 'false' otherwise).
        """
        if e.data:  # Hovered
            self.bgcolor = lighten_color(DARK_BLUE_GREY, 0.2)
        else:  # Not hovered
            self.bgcolor = DARK_BLUE_GREY
        self.update()