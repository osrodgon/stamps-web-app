"""
Stamps manager page for administering the master stamp catalog.

Provides a full-featured data table for browsing, filtering, and managing
stamp issues. Includes a debounced search field, slide-out navigation drawer,
and session-based user preferences.
"""

import asyncio

import flet as ft

from components.templates.standard_page import StandardPage
from components.layout.app_header import AppHeader
from core.translations import _
from components.buttons.icon_button import IconButton
from components.colors import DARK_BLUE_GREY
from components.form.text_field import APP_HEADER, TextField
from components.layout.vertical_line import VerticalLine
from components.layout.app_drawer import AppDrawer
from components.table.issue_table_app import IssueTableApp
from services.stamp_issue_service import StampIssueService
from settings import USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME


class StampsManagerPage(StandardPage):
    """
    The stamps manager page for the Stamps web application.
    
    Provides administrative access to manage the master stamp catalog.
    Features an AppHeader with menu icon, page title, and vertical separator.
    Includes a debounced filter field that searches by name or year.
    
    The page uses StandardPage as its base, providing:
    - AppHeader with left-aligned controls (menu, title, separator, filter)
    - Main content area for the IssueTable
    - Slide-out AppDrawer navigation
    
    Attributes:
        header: The AppHeader containing menu, title, separator, and filter.
    """
    
    header: AppHeader
        
    def __init__(self, page: ft.Page):
        """Initialize the StampsManagerPage with header, filter, table, and drawer.
        
        Args:
            page: The Flet page instance.
        """
        super().__init__(
            page=page,
            header_height=80,
        )
        
        self._filter_task: asyncio.Task | None = None
        
        # Set AppHeader first
        self.header = self.set_app_header(AppHeader())
        
        # Controls for the left area of the header
        menu_icon = IconButton(icon=ft.Icons.MENU, bgcolor=DARK_BLUE_GREY, on_click=self.menu_clicked)
        menu_text = ft.Text(
            _("stamps.stamps_manager_title"),
            color = ft.Colors.WHITE,
            font_family="Roboto-Bold",
            size=20
        )
        separator = VerticalLine(thickness=1, length=30, color=ft.Colors.GREY_700)
        series_year_filter = TextField(
            label=_("filter.series_year"),
            field_style=APP_HEADER,
            tooltip=  _("filter.series_year_tooltip_header") + "\n"  + "\n" \
                    + _("filter.series_year_tooltip_1") + "\n" \
                    + _("filter.series_year_tooltip_2") + "\n" \
                    + _("filter.series_year_tooltip_3") + "\n" \
                    + _("filter.series_year_tooltip_4"),
            on_change=self._filter_series_year,
            width=200
            
        )
        
        # Add controls to header
        self.header.add_left(menu_icon)
        self.header.add_left(menu_text)
        self.header.add_left(separator)
        self.header.add_left(series_year_filter)
        
        # Create the drawer
        self.drawer = AppDrawer(on_logout=self.request_logout)
        
        # Create the content area
        self._table: IssueTableApp = IssueTableApp(service=StampIssueService())
        self.content_area = ft.Column(
            [self._table],
            expand=True,
            expand_loose=True,
            margin=15
        )
        
        # Use self.main to hold both Drawer and Content in a Row
        self.main.content = ft.Stack(
            controls=[
                self.content_area,
                self.drawer
            ],
            expand=True
        )
                
        page.run_task(self.read_prefs)
        
    async def menu_clicked(self, e: ft.ControlEvent) -> None:
        """Toggle the slide-out navigation drawer open or closed."""
        self.log.debug("Hamburger menu clicked")
        
        if self.drawer.offset.x == 0:
            # Hide: Slide left
            self.drawer.offset = ft.Offset(-1, 0)
        else:
            # Show: Slide back
            self.drawer.offset = ft.Offset(0, 0)
        self.drawer.update()
        
    async def read_prefs(self) -> None:
        """Load user preferences from SharedPreferences and initialize table data."""
        prefs = ft.SharedPreferences()

        user_first_name = await prefs.get(USER_FIRST_NAME)
        user_last_name = await prefs.get(USER_LAST_NAME)
        user_email = await prefs.get(USER_EMAIL)

        self.drawer.update_data(user_first_name, user_last_name, user_email)
        await self._table.load()
        
    async def _filter_series_year(self, e: ft.ControlEvent) -> None:
        """Handle filter text changes with 300ms debounce.

        Cancels any pending search task and starts a new debounced one,
        ensuring only the final value triggers an API call.
        Args:
            e: Control event containing the new filter value.
        """
        if self._filter_task:
            self._filter_task.cancel()
        self._filter_task = asyncio.create_task(self._debounced_search(e.control.value))

    async def _debounced_search(self, value: str) -> None:
        """Wait 300ms then trigger a table reload with the current filter.
        
        Args:
            value: The raw filter string (text, number, or pattern).
        """
        await asyncio.sleep(0.3)
        self.log.debug(f"Aplying filter: {value}")
        await self._table.load(search=value)