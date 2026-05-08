"""
Color constants and utilities for the Flet application.

This module defines a centralized set of color values used throughout the
application's UI components. Colors are named based on their actual
appearance (e.g., SKY_BLUE, SLATE_GREY) rather than their usage.

The module includes:
- Button colors with hover states
- Text colors
- Text field border colors
- Brand-specific colors for decorative elements

Colors can be imported directly by other components
(e.g., `from core.components.colors import SKY_BLUE`).
"""

import flet as ft


def lighten_color(hex_color, amount=0.2):
    """
    Creates a lighter shade of a given hex color.

    Mixes the input color with white based on the specified amount,
    producing a lighter variant useful for hover states or disabled
    appearances.

    Args:
        hex_color (str): The base color in hex format (e.g., '#5898d4' or '5898d4').
        amount (float, optional): The amount of white to blend in, as a value
            between 0 and 1. Defaults to 0.2 (20% lighter).

    Returns:
        str: The lightened color as a hex string (e.g., '#7fb3e0').
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    
    return f'#{r:02x}{g:02x}{b:02x}'

# --- Button Colors ---

#: Medium sky blue (#5898d4) - used for primary buttons and links.
SKY_BLUE = "#5898d4"
#: Lighter variant of SKY_BLUE for hover states (30% lightened).
SKY_BLUE_HOVER = lighten_color(SKY_BLUE, 0.3)

#: Cool slate grey (#707282) - used for secondary/text buttons.
SLATE_GREY = "#707282"
#: Lighter variant of SLATE_GREY for hover states (30% lightened).
SLATE_GREY_HOVER = lighten_color(SLATE_GREY, 0.3)


# --- Text Colors ---

#: Standard body text color (Flet GREY_700).
GREY_700 = ft.Colors.GREY_700


# --- Text Field Colors ---

#: Default border color for text fields (Flet BLUE_GREY_100).
BLUE_GREY_100 = ft.Colors.BLUE_GREY_100
#: Focused border color for text fields (Flet BLUE_700).
BLUE_700 = ft.Colors.BLUE_700

# --- Brand Colors ---

#: Dark navy blue (#2c4869) - used for brand title text.
NAVY_DARK = "#2c4869"
#: Dark slate (#364153) - used for brand subtitle text.
SLATE_DARK = "#364153"
#: Light silver-grey (#99a1af) - used for decorative horizontal lines.
SILVER_LIGHT = "#99a1af"


