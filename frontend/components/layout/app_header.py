"""
App header component for authenticated pages.

This module provides the AppHeader component used in authenticated pages
like Stamps Manager Page and Collections Page. It provides a three-area
layout (left, center, right) for header content.
"""

import flet as ft
from core.logger import Logger
from components.colors import DARK_BLUE_GREY

class AppHeader(ft.Container, Logger):
    """
    A header component with three alignment areas: left, center, and right.
    
    Used in StandardPage for authenticated pages like:
    - Stamps Manager Page
    - Collections Page
    
    Layout:
    - Left area: Left-aligned content (e.g., back button)
    - Center area: Center-aligned content (typically the page title)
    - Right area: Right-aligned content (e.g., logout, user menu)
    
    Attributes:
        left (ft.Container): Container for left-aligned content.
        center (ft.Container): Container for center-aligned content.
        right (ft.Container): Container for right-aligned content.
    """
    
    left_area: ft.Container
    center_area: ft.Container
    right_area: ft.Container
    
    def __init__(self, left_content=None, center_content=None, right_content=None, height: int=80):
        """
        Initialize AppHeader with three areas.
        
        Args:
            title (str, optional): Page title to display in center area.
            left_content (ft.Control, optional): Control for left area.
            right_content (ft.Control, optional): Control for right area.
            height (int, optional): Height of the header (default 80)
        """
        super().__init__(padding=ft.Padding.only(left=10, right=10))
        self.height = height

        self.bgcolor = DARK_BLUE_GREY
        
        # Left area
        self.left_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
        
        # Center area  
        self.center_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
        
        # Right area
        self.right_area = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        self.content = ft.Row(
            controls=[self.left_area, self.center_area, self.right_area],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    # --- Left Area ---
    def add_left(self, control: ft.Control):
        """Add a control to the left area."""
        self.left_area.controls = self.left_area.controls + [control]
    
    def clear_left(self):
        """Remove all controls from the left area."""
        self.left_area.controls = []
    
    # --- Center Area ---
    def add_center(self, control: ft.Control):
        """Add a control to the center area."""
        self.center_area.controls = self.center_area.controls + [control]
    
    def clear_center(self):
        """Remove all controls from the center area."""
        self.center_area.controls = []
    
    # --- Right Area ---
    def add_right(self, control: ft.Control):
        """Add a control to the right area."""
        self.right_area.controls = self.right_area.controls + [control]
    
    def clear_right(self):
        """Remove all controls from the right area."""
        self.right_area.controls = []