import flet as ft
from core.base_ui import BaseUI

class StandardPage(ft.View, BaseUI):
    """
    A base page template with header and main content areas.
    
    Used as the base class for authenticated pages like:
    - Stamps Manager Page
    - Collections Page
    
    Layout:
    - Header: Contains AppHeader (to be created), fixed height (60px), expands horizontally
    - Main: Expands to fill remaining space (vertical & horizontal)
    
    Attributes:
        header (ft.Container): Header section containing AppHeader.
        main (ft.Container): Main content area that expands.
    """
    
    header: ft.Container
    main: ft.Container
    main_page: ft.Page
    
    def __init__(self, page: ft.Page, header_height: int = 80):
        """
        Initialize StandardPage with header and main containers.
        
        Args:
            page: The Flet page instance.
            header_height: Height of the header in pixels. Default: 60.
        """
        self.main_page = page
        
        # Header - fixed height at top, contains AppHeader (to be created)
        self.header = ft.Container(
            height=header_height,
            expand=False,
        )
        
        # Main - expands to fill remaining space
        self.main = ft.Container(
            expand=True,
        )
        
        super().__init__(
            padding=0,
            controls=[
                ft.Column(
                    controls=[self.header, self.main],
                    expand=True,
                    spacing=0
                )
            ]
        )
    
    def set_app_header(self, app_header):
        """Set the AppHeader control in the header container.
        
        Args:
            app_header: The AppHeader control to display in the header.
        """
        self.header.content = app_header
        