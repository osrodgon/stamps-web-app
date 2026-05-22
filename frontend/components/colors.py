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
(e.g., `from components.colors import SKY_BLUE`).
"""

import flet as ft

def lighten_color(hex_color: str, amount: float = 0.2) -> str:
    """Creates a lighter shade of a given hex color by blending with white."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    
    return f'#{r:02x}{g:02x}{b:02x}'

# --- Button Colors ---

#: Medium sky blue (#5898d4) - used for primary buttons and links.
SKY_BLUE: str = "#5898d4"
#: Lighter variant of SKY_BLUE for hover states (10% lightened).
SKY_BLUE_HOVER: str = lighten_color(SKY_BLUE, 0.1)
#: Lighter variant of SKY_BLUE for hover states (30% lightened).
SKY_BLUE_DISABLED: str = lighten_color(SKY_BLUE, 0.3)

#: Cool slate grey (#707282) - used for secondary/text buttons.
SLATE_GREY: str = "#707282"
#: Lighter variant of SLATE_GREY for hover states (20% lightened).
SLATE_GREY_HOVER: str = lighten_color(SLATE_GREY, 0.2)

#: Red (#E53935) - used for destructive/danger actions.
RED: str = "#E53935"
#: Darker red (#C62828) - hover state for RED.
RED_HOVER: str = "#C62828"
#: Light grey (#BDBDBD) - disabled state for RED buttons.
RED_DISABLED: str = "#BDBDBD"

# --- Text Colors ---

#: Standard body text color (Flet GREY_700).
GREY_700: str = ft.Colors.GREY_700


# --- Text Field Colors ---

#: Default border color for text fields (Flet BLUE_GREY_100).
BLUE_GREY_100: str = ft.Colors.BLUE_GREY_100
#: Focused border color for text fields (Flet BLUE_700).
BLUE_700: str = ft.Colors.BLUE_700

# --- Brand Colors ---

#: Dark navy blue (#2c4869) - used for brand title text.
NAVY_DARK: str = "#2c4869"
#: Dark slate (#364153) - used for brand subtitle text.
SLATE_DARK: str = "#364153"
#: Light silver-grey (#99a1af) - used for decorative horizontal lines.
SILVER_LIGHT: str = "#99a1af"

#: Dark blue-grey (#1e2b3c) - used for dark UI backgrounds.
DARK_BLUE_GREY: str = "#1e2b3c"
#: Teal (#00bfa5) - used for accent icons (e.g., lightbulb icon).
PRIMARY_ACCENT: str = "#00bfa5"
#: Blue (#1976d2) - used for issue names and links.
TEXT_BLUE: str = "#1976d2"
#: Red (#ef5350) - used for delete/action buttons.
DELETE_RED: str = "#ef5350"
#: Light grey (#f5f5f5) - used for light backgrounds.
BG_LIGHT: str = "#f8fafc"
#: Very light grey-blue (#f0f4f8) - gradient start for page backgrounds.
BG_GRADIENT_START: str = "#f0f4f8"
#: Light grey-blue (#e2e8f0) - gradient end for page backgrounds.
BG_GRADIENT_END: str = "#e2e8f0"


#: Subtle grey (#f1f5f9) - used for alternating table row backgrounds.
BG_ALT: str = "#f1f5f9"

# --- Table Colors ---

#: Dark navy (#232F3E) - used for table header background.
HEADER_BG: str = "#232F3E"
#: Light grey (#EEEEEE) - used for table row dividers.
ROW_BORDER: str = "#D0D0D0"
#: Medium grey (#666666) - used for icon colors (calendar, navigation).
ICON_GREY: str = "#666666"
#: Near white (#FAFAFA) - used for expansion panel background.
EXPANSION_BG: str = "#FAFAFA"
#: Darker Grey (#E8E8E8) - Used for row hovering
ROW_HOVER: str = "#E8E8E8"
#: Muted blue-grey (#3d4c5d) - used for RangeSlider inactive track.
SLIDER_INACTIVE: str = "#3d4c5d"

#: Near black (#313131) - used for stamp image background in dialogs and thumbnails.
DARK_IMG_BG: str = "#313131"

# --- Slider Visual Constants ---

#: Multiplier for thumb radius to compute aura circle radius (1.8x thumb).
AURA_RADIUS_MULTIPLIER: float = 1.8
#: Opacity for the aura fill around the active slider thumb.
AURA_OPACITY: float = 0.25
#: Scale factor for thumb enlargement while dragging (1.5x thumb radius).
DRAG_THUMB_SCALE: float = 1.5

