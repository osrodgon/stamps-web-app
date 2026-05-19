"""
Stamps manager page for administering the master stamp catalog.

Provides a full-featured data table for browsing, filtering, and managing
stamp issues. Includes a debounced search field, a YearRangeSelector for
year-range filtering, slide-out navigation drawer, and session-based user
preferences. Pagination is automatically reset to page 1 when filters change.
"""

import asyncio

import flet as ft
import requests

from components.templates.standard_page import StandardPage
from components.layout.app_header import AppHeader
from core.translations import _
from components.buttons.icon_button import IconButton
from components.colors import BG_GRADIENT_END, BG_GRADIENT_START, DARK_BLUE_GREY
from components.form.text_field import APP_HEADER, TextField
from components.layout.vertical_line import VerticalLine
from components.layout.app_drawer import AppDrawer
from components.table.issue_table_app import IssueTableApp
from components.form.year_range_selector import YearRangeSelector
from services.issue_service import IssueService
from settings import USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME


class StampsManagerPage(StandardPage):
    """The stamps manager page for the Stamps web application.

    Provides administrative access to manage the master stamp catalog.
    Features an AppHeader with menu icon, page title, vertical separator,
    debounced name filter, and YearRangeSelector.

    The page uses StandardPage as its base, providing:
    - AppHeader with left-aligned controls (menu, title, separator, filter)
    - YearRangeSelector for year-range filtering
    - Main content area for the IssueTable
    - Slide-out AppDrawer navigation
    - Debounced (300ms) name/year text filter with pagination reset
    - Debounced (300ms) year range slider with pagination reset

    Attributes:
        header: The AppHeader containing menu, title, separator, and filter.
        drawer: The slide-out navigation drawer.
    """
    
    header: AppHeader
        
    def __init__(self, page: ft.Page) -> None:
        """Initialize the StampsManagerPage with header, filter, table, and drawer.

        Constructs the AppHeader with menu icon, title, separator, text
        filter field, and YearRangeSelector. Creates the AppDrawer for
        navigation and the IssueTableApp for displaying stamp issues.
        Schedules asynchronous loading of user preferences on startup.

        Args:
            page: The Flet page instance.
        """
        super().__init__(
            page=page,
            header_height=80,
        )
        
        self._filter_task: asyncio.Task | None = None
        self._year_range_task: asyncio.Task | None = None
        self._issue_service: IssueService = IssueService()
        
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
        self._year_selector = YearRangeSelector(
            step=5, 
            track_height=1, 
            width=250, 
            top_padding=26,
            on_change=self._year_range_selector
        )
        
        # Add controls to header
        self.header.add_left(menu_icon)
        self.header.add_left(menu_text)
        self.header.add_left(separator)
        self.header.add_left(series_year_filter)
        self.header.add_left(self._year_selector)
        
        # Create the drawer
        self.drawer = AppDrawer(on_logout=self.request_logout)
        
        # Create the content area
        self._table: IssueTableApp = IssueTableApp(service=self._issue_service)
        self.content_area = ft.Column(
            [self._table],
            expand=True,
            expand_loose=True,
            margin=15
        )
        
        # Stack content area and drawer for overlay behavior
        self.main.content = ft.Stack(
            controls=[
                self.content_area,
                self.drawer
            ],
            expand=True
        )
        self.main.gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[BG_GRADIENT_START, BG_GRADIENT_END],
        )
                
        page.run_task(self.read_prefs)
        
    async def menu_clicked(self, e: ft.ControlEvent) -> None:
        """Toggle the slide-out navigation drawer open or closed.

        Animates the drawer offset between hidden (-1, 0) and visible (0, 0).

        Args:
            e: The click event from the menu IconButton.
        """
        self.log.debug("Hamburger menu clicked")
        
        if self.drawer.offset.x == 0:
            # Hide: Slide left
            self.drawer.offset = ft.Offset(-1, 0)
        else:
            # Show: Slide back
            self.drawer.offset = ft.Offset(0, 0)
        self.drawer.update()
        
    async def read_prefs(self) -> None:
        """Load user preferences from SharedPreferences and initialize page data.

        Fetches user profile data for the drawer, loads the initial issue
        table data, and initializes the YearRangeSelector with the full
        range of available years from the backend API.
        """
        prefs = ft.SharedPreferences()

        user_first_name = await prefs.get(USER_FIRST_NAME)
        user_last_name = await prefs.get(USER_LAST_NAME)
        user_email = await prefs.get(USER_EMAIL)

        self.drawer.update_data(user_first_name, user_last_name, user_email)
        await self._table.load()

        # Fetch years and initialize the year range selector
        response = await self._issue_service.get_years()
        if response and response.status_code == requests.codes.ok:
            years_data: list[dict] = response.json().get("data", [])
            years: list[int] = [item["year"] for item in years_data]
            if years:
                raw_min: int = min(years)
                raw_max: int = max(years)
                self._year_selector.set_range(
                    min_year=self._round_down(raw_min),
                    max_year=self._round_up(raw_max),
                    start=self._round_down(raw_min),
                    end=self._round_up(raw_max),
                )
        
    async def _filter_series_year(self, e: ft.ControlEvent) -> None:
        """Handle filter text changes with 300ms debounce.

        Cancels any pending search task and starts a new debounced one,
        ensuring only the final value triggers an API call. Resets
        pagination to page 1 before fetching.

        Args:
            e: Control event containing the new filter value.
        """
        if self._filter_task:
            self._filter_task.cancel()
        self._filter_task = asyncio.create_task(self._debounced_search(e.control.value))

    async def _debounced_search(self, value: str) -> None:
        """Wait 300ms then trigger a table reload with the current filter.

        Resets pagination to page 1 to avoid empty result pages
        when the filtered dataset is smaller than the current page.

        Args:
            value: The raw filter string (text, number, or pattern).
        """
        await asyncio.sleep(0.3)
        self.log.debug(f"Aplying filter: {value}")
        await self._table.load(search=value, reset_page=True)

    @staticmethod
    def _round_down(year: int) -> int:
        """Round a year down to the nearest multiple of 5.

        1852 → 1850, 1857 → 1855, 1840 → 1840
        """
        return (year // 5) * 5

    @staticmethod
    def _round_up(year: int) -> int:
        """Round a year up to the nearest multiple of 5.

        1852 → 1855, 1857 → 1860, 1840 → 1840
        """
        return ((year + 4) // 5) * 5

    async def _year_range_selector(self, start: int, end: int) -> None:
        """Handle year range slider changes with 300ms debounce.

        Cancels any pending year range task and starts a new debounced one,
        ensuring only the final slider position triggers an API call.
        Resets pagination to page 1 before fetching.

        Args:
            start: The selected minimum year.
            end: The selected maximum year.
        """
        self.log.debug(f"Year range selected: {start} - {end}")
        if self._year_range_task:
            self._year_range_task.cancel()
        self._year_range_task = asyncio.create_task(self._debounced_year_range(start, end))

    async def _debounced_year_range(self, start: int, end: int) -> None:
        """Wait 300ms then apply the year range filter.

        Resets pagination to page 1 to avoid empty result pages
        when the filtered dataset is smaller than the current page.

        Args:
            start: The selected minimum year.
            end: The selected maximum year.
        """
        await asyncio.sleep(0.3)
        self._table.set_year_filter(f"{start}-{end}")