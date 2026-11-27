"""
HorizontalLine module.

Provides a reusable horizontal line component built on Flet's Container.
"""

import flet as ft


class HorizontalLine(ft.Container):
    """
    A horizontal line component implemented as a Flet Container.
    
    This component renders a simple horizontal line with customizable thickness,
    length, and color. It uses a Container with border radius for rounded edges.
    
    Attributes:
        thickness (int): The height of the line in pixels.
        length (int): The width of the line in pixels.
        color (ft.Colors): The color of the line.
    """
    
    def __init__(self, thickness=2, length=10, color=ft.Colors.BLACK):
        """
        Initialize a HorizontalLine component.
        
        Args:
            thickness (int, optional): The height/thickness of the line in pixels.
                Defaults to 2.
            length (int, optional): The width/length of the line in pixels.
                Defaults to 10.
            color (ft.Colors, optional): The color of the line.
                Defaults to ft.Colors.BLACK.
        
        Example:
            >>> line = HorizontalLine(thickness=3, length=48, color=ft.Colors.BLUE)
            >>> isinstance(line, ft.Container)
            True
        """
        super().__init__(
            height=thickness,
            width=length,
            bgcolor=color,
            border_radius=5
        )
        