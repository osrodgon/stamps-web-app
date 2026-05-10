import flet as ft

from core.logger import Logger
from components.colors import HEADER_BG

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
        super().__init__()
        self.height = height
        self.bgcolor = HEADER_BG
        
        # Left area - left aligned
        self.left_area = ft.Container(
            alignment=ft.Alignment.CENTER_LEFT,
            expand=True
        )
        
        # Center area - Centered
        self.center_area = ft.Container(
            alignment=ft.Alignment.CENTER,
            expand=True
        )
        
        # Right area - right aligned
        self.right_area = ft.Container(
            alignment=ft.Alignment.CENTER_RIGHT,
            expand=True
        )
        
        self.content = ft.Row(
            controls=[self.left_area, self.center_area, self.right_area],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
        
        # Set initial content if provided
        if left_content:
            self.left_area.content = left_content
        if center_content:
            self.center_area.content = center_content
        if right_content:
            self.right_area.content = right_content
    
    # --- Left Area Methods ---
    
    def add_left(self, control: ft.Control):
        """Add a control to the left area.
        
        Args:
            control: The Flet control to add.
        """
        self.left_area.content = control
    
    def clear_left(self):
        """Remove all content from the left area."""
        self.left_area.content = None
    
    # --- Center Area Methods ---
    
    def add_center(self, control: ft.Control):
        """Add a control to the center area.
        
        Args:
            control: The Flet control to add.
        """
        self.center_area.content = control
    
    def clear_center(self):
        """Remove all content from the center area."""
        self.center_area.content = None
    
    # --- Right Area Methods ---
    
    def add_right(self, control: ft.Control):
        """Add a control to the right area.
        
        Args:
            control: The Flet control to add.
        """
        self.right_area.content = control
    
    def clear_right(self):
        """Remove all content from the right area."""
        self.right_area.content = None