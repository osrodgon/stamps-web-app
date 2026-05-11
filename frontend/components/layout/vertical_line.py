import flet as ft

class VerticalLine(ft.Container):
    """
    A vertical line component implemented as a Flet Container.
    
    This component renders a simple vertical line with customizable thickness,
    length, and color. It uses a Container with border radius for rounded edges.
    
    Attributes:
        thickness (int): The width of the line in pixels.
        length (int): The height of the line in pixels.
        color (ft.Colors): The color of the line.
    """
    
    def __init__(self, thickness=2, length=100, color=ft.Colors.BLACK):
        """
        Initialize a VerticalLine component.
        
        Args:
            thickness (int, optional): The width/thickness of the line in pixels.
                Defaults to 2.
            length (int, optional): The height/length of the line in pixels.
                Defaults to 100.
            color (ft.Colors, optional): The color of the line.
                Defaults to ft.Colors.BLACK.
        """
        super().__init__(
            width=thickness,      # Swap: width becomes thickness
            height=length,         # Swap: height becomes length
            bgcolor=color,
            border_radius=5
        )
        