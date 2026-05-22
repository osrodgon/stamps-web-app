"""
Collections page for viewing user stamp collections.

This module provides the CollectionsPage view that displays a user's
stamp collections. Features include:
- App header with menu icon and page title
- Slide-out navigation drawer
- Scrollable content area for collection display
"""

import flet as ft

from components.templates.standard_page import StandardPage
from components.layout.app_header import AppHeader
from core.translations import _
from components.buttons.icon_button import IconButton
from components.colors import DARK_BLUE_GREY
from components.layout.vertical_line import VerticalLine
from components.layout.app_drawer import AppDrawer
from settings import USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME
from components.constants import HEADER_HEIGHT


class CollectionsPage(StandardPage):
    """The collections page for displaying user stamp collections.
    
    This page allows authenticated users to view their stamp collections.
    It features:
    - AppHeader with menu icon, title, and vertical separator
    - Slide-out navigation drawer (AppDrawer) with user profile
    - Main content area for displaying collections
    
    The page extends StandardPage which provides the base layout with
    header and main content areas.
    
    Attributes:
        header: The AppHeader containing menu, title, and separator.
        drawer: The AppDrawer for navigation.
        content_area: The main content column for collections display.
    """    
    header: AppHeader
    
    def __init__(self, page: ft.Page):
        """Initialize the StampsManagerPage.
        
        Args:
            page: The Flet page instance.
        """
        super().__init__(
            page=page,
            header_height=HEADER_HEIGHT,
        )
        
        # Set AppHeader first
        self.header = self.set_app_header(AppHeader())

        menu_icon = IconButton(icon=ft.Icons.MENU, bgcolor=DARK_BLUE_GREY, on_click=self.menu_clicked)
        menu_text = ft.Text(
            _("collections.title"),
            color = ft.Colors.WHITE,
            font_family="Roboto-Bold",
            size=20
        )
        separator = VerticalLine(thickness=1, length=30, color=ft.Colors.GREY_700)
        
        # Add controls to header
        self.header.add_left(menu_icon)
        self.header.add_left(menu_text)
        self.header.add_left(separator)
        
        # Create the drawer
        self.drawer = AppDrawer(on_logout=self.request_logout)
        
        # Create the content area
        self.content_area = ft.Column(
            [
                ft.Text(_("collections.title"), size=24, weight="bold"),
            # You can add other controls here later
            ], 
            expand=True, 
            scroll=ft.ScrollMode.ADAPTIVE,
        )
        
        # Use self.main to hold both Drawer and Content in a Row
        self.main.content = ft.Stack(
            controls=[
                self.content_area,
                self.drawer
            ],
            expand=True,
        )
        
        page.run_task(self.read_prefs)
        
    async def menu_clicked(self, e):
        self.log.debug("Hamburger menu clicked")
        
        if self.drawer.offset.x == 0:
            # Hide: Slide left
            self.drawer.offset = ft.Offset(-1, 0)
        else:
            # Show: Slide back
            self.drawer.offset = ft.Offset(0, 0)
        self.drawer.update()
        
    async def read_prefs(self):
        prefs = ft.SharedPreferences()
        
        user_first_name = await prefs.get(USER_FIRST_NAME)
        user_last_name = await prefs.get(USER_LAST_NAME)
        user_email = await prefs.get(USER_EMAIL)
        
        self.drawer.update_data(user_first_name, user_last_name, user_email)
        