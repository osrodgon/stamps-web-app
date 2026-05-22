"""
App header component for authenticated pages.

Provides a three-area layout bar (left, center, right) used in
StandardPage-based pages like Stamps Manager and Collections.
Controls are added via add_left/add_center/add_right and rendered
inside expandable Rows with SPACE_BETWEEN distribution.
"""

import flet as ft
from core.logger import Logger
from components.colors import DARK_BLUE_GREY
from components.constants import HEADER_HEIGHT, STANDARD_PADDING


class AppHeader(ft.Container, Logger):
    """
    A header component with three alignment areas: left, center, and right.

    Used in StandardPage for authenticated pages like:
    - Stamps Manager Page
    - Collections Page

    Layout:
    - Left area:   Left-aligned controls (menu icon, title, filter, separator).
                   Does NOT expand — wraps content.
    - Center area: Center-aligned content (typically empty).
                   Expands to fill remaining space.
    - Right area:  Right-aligned controls (user menu, logout).
                   Does NOT expand — wraps content.

    After calling add_left/add_center/add_right, call update_header()
    on the parent page to re-render.

    Attributes:
        left_area (ft.Row):  Row for left-aligned header controls.
        center_area (ft.Row): Row for center-aligned header controls.
        right_area (ft.Row):  Row for right-aligned header controls.
    """

    left_area: ft.Row
    center_area: ft.Row
    right_area: ft.Row

    def __init__(self, height: int = HEADER_HEIGHT) -> None:
        """Initialize AppHeader with three empty area Rows.

        Args:
            height: Height of the header in pixels (default 80).
        """
        super().__init__(padding=ft.Padding.only(left=STANDARD_PADDING, right=STANDARD_PADDING))
        self.height = height

        self.bgcolor = DARK_BLUE_GREY

        # Left area — left-aligned, natural width
        self.left_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Center area — centered, expands to fill space
        self.center_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        # Right area — right-aligned, natural width
        self.right_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Row(
            controls=[self.left_area, self.center_area, self.right_area],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    
    # --- Left Area ---

    def add_left(self, control: ft.Control) -> None:
        """Append a control to the left area."""
        self.left_area.controls = self.left_area.controls + [control]

    def clear_left(self) -> None:
        """Remove all controls from the left area."""
        self.left_area.controls = []

    # --- Center Area ---

    def add_center(self, control: ft.Control) -> None:
        """Append a control to the center area."""
        self.center_area.controls = self.center_area.controls + [control]

    def clear_center(self) -> None:
        """Remove all controls from the center area."""
        self.center_area.controls = []

    # --- Right Area ---

    def add_right(self, control: ft.Control) -> None:
        """Append a control to the right area."""
        self.right_area.controls = self.right_area.controls + [control]

    def clear_right(self) -> None:
        """Remove all controls from the right area."""
        self.right_area.controls = []