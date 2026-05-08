"""
BrandCollectibles module.

Provides a branding component displaying "Collectibles" and "Your Stamps World"
text with decorative horizontal lines, positioned at the bottom center of the screen.
"""

import flet as ft
from core.components.horizontal_line import HorizontalLine
from core.components.colors import NAVY_DARK, SLATE_DARK, SILVER_LIGHT
from core.translations import _


class BrandCollectibles(ft.Container):
    """
    A branding component that displays the application's brand text with decorative elements.
    
    This component renders a centered branding section at the bottom of the screen
    featuring the "Collectibles" title and "Your Stamps World" subtitle, flanked by
    horizontal decorative lines on each side.
    
    Attributes:
        collectibles_text (ft.Text): The main brand title text component.
        stamps_world_text (ft.Text): The subtitle text component.
    """
    
    collectibles_text: ft.Text
    stamps_world_text: ft.Text
    
    def __init__(self):
        """
        Initialize the BrandCollectibles component.
        
        Sets up the branding layout with:
        - A large "Collectibles" title text
        - A "Your Stamps World" subtitle with horizontal lines on each side
        - Bottom-center alignment with fixed positioning
        
        The component uses translated text strings and predefined color constants
        for consistent theming across the application.
        """
        super().__init__(left=0, right=0, bottom=35, alignment=ft.Alignment.BOTTOM_CENTER)
        
        line = HorizontalLine(thickness=2, length=48, color=SILVER_LIGHT)
        self.collectibles_text = ft.Text(
            _("branding.collectibles"), 
            size=48,
            color=NAVY_DARK,
            font_family="Roboto-Black",
            style=ft.TextStyle(letter_spacing=4.5),
            align=ft.Alignment.CENTER
        )
        self.stamps_world_text = ft.Text(
            _("branding.your_stamps_world"),
            color=SLATE_DARK,
            size=19,
            font_family="Roboto",
            margin=ft.Margin(left=25, right=25)
        )
        
        self.content = ft.Column(
            controls = [
                self.collectibles_text,
                ft.Row(
                    controls = [
                        line,
                        self.stamps_world_text,
                        line
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=False
                )
            ]
        )

    def update(self):
        """
        Update the text content with current translations.
        
        Refreshes both the collectibles title and stamps world subtitle
        with the latest translated strings. Call this method when the
        application language changes to update the displayed text.
        """
        self.collectibles_text.value = _("branding.collectibles")
        self.stamps_world_text.value = _("branding.your_stamps_world")
        