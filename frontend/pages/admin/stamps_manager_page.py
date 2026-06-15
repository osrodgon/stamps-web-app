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
from components.form.dialogs.issue_form import IssueForm
from components.form.dialogs.stamp_form import StampForm
from core.severity import Severity
from services.issue_service import IssueService
from settings import USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME
from components.constants import HEADER_HEIGHT, DEBOUNCE_DELAY


class StampsManagerPage(StandardPage):
    """The stamps manager page for the Stamps web application.

    Provides administrative access to manage the master stamp catalog.
    Features an AppHeader with menu icon, page title, vertical separator,
    debounced name filter, and YearRangeSelector.

    The page uses StandardPage as its base, providing:
    - AppHeader with left-aligned controls (menu, title, separator, filter)
      and right-aligned add-issue button
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
        filter field, YearRangeSelector, and add-issue button. Creates
        the AppDrawer for navigation and the IssueTableApp for displaying
        stamp issues. Schedules asynchronous loading of user preferences
        on startup.

        Args:
            page: The Flet page instance.
        """
        super().__init__(
            page=page,
            header_height=HEADER_HEIGHT,
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

        # Right area: Add new issue button
        add_issue_btn = IconButton(
            icon=ft.Icons.ADD,
            bgcolor=DARK_BLUE_GREY,
            on_click=self._handle_add_issue,
            tooltip=_("issues.add_tooltip")
        )
        self.header.add_right(add_issue_btn)

        # Create the drawer
        self.drawer = AppDrawer(
            on_logout=self.request_logout,
            on_profile=self.request_profile,
            on_settings=self.request_settings
        )
        
        # Create the content area
        self._table: IssueTableApp = IssueTableApp(
            service=self._issue_service,
            on_edit_stamp=self._handle_edit_stamp,
            on_delete_stamp=self._handle_delete_stamp,
            on_edit_issue=self._handle_edit_issue,
            on_delete_issue=self._handle_delete_issue,
            on_add_stamp=self._handle_add_stamp,
        )
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
        await asyncio.sleep(DEBOUNCE_DELAY)
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
        await asyncio.sleep(DEBOUNCE_DELAY)
        self._table.set_year_filter(f"{start}-{end}")

    def _handle_edit_stamp(self, stamp_id: int) -> None:
        """Handle stamp edit action — stub for future implementation.

        Args:
            stamp_id: The ID of the stamp to edit.
        """
        self.log.debug(f"Edit stamp {stamp_id}")

    def _handle_delete_stamp(self, stamp_id: int, issue_id: int) -> None:
        """Delete a stamp, show notification, and refresh stamps.

        Args:
            stamp_id: The ID of the stamp to delete.
            issue_id: The ID of the parent issue for post-delete refresh.
        """
        self.log.debug(f"Delete stamp {stamp_id} from issue {issue_id}")

        page = self.page

        async def do_delete() -> None:
            """Send DELETE request, show notification, and refresh stamps.

            Runs as a background task via ``page.run_task()``. On success,
            shows a green notification and re-fetches the affected issue's
            stamps. On failure, shows a red notification with the HTTP status
            code logged for debugging.
            """
            try:
                response = await self._issue_service.delete_stamp(stamp_id)
                if response and response.status_code == requests.codes.ok:
                    self.log.debug(f"Stamp {stamp_id} deleted successfully")
                    await self.show_notification(_("stamps.delete_success"), severity=Severity.SUCCESS, duration=1500)
                    page.update()
                    await self._table._fetch_stamps_for_row(issue_id)
                else:
                    status_code = response.status_code if response else "no response"
                    self.log.error(f"Delete stamp failed: {status_code}")
                    await self.show_notification(_("stamps.delete_error"), severity=Severity.ERROR, duration=1500)
                    page.update()
            except Exception as ex:
                self.log.error(f"Delete stamp error: {ex}")
                await self.show_notification(_("messages.unexpected_error"), severity=Severity.ERROR)
                page.update()

        self.page.run_task(do_delete)

    def _handle_edit_issue(self, issue_id: int) -> None:
        """Reload table after an issue has been edited.

        Called from IssueDetailCard after a successful save of edit mode.

        Args:
            issue_id: The ID of the issue that was updated.
        """
        self.log.debug(f"Issue {issue_id} updated.")
        # self.page.run_task(self._table.load, reset_page=True)

    def _handle_delete_issue(self, issue_id: int) -> None:
        """Delete an issue, show notification, and reload the table.

        Sends a DELETE request to the backend and refreshes the table
        on success. The backend cascade-deletes all stamps belonging
        to this issue automatically.

        Args:
            issue_id: The ID of the issue to delete.
        """
        self.log.debug(f"Delete issue {issue_id}")

        page = self.page

        async def do_delete() -> None:
            """Send DELETE request, show notification, and reload table.

            Runs as a background task via ``page.run_task()``. On success,
            shows a green notification and reloads the issue table. On
            failure, shows a red notification with the HTTP status code
            logged for debugging.
            """
            try:
                response = await self._issue_service.delete_issue(issue_id)
                if response and response.status_code == requests.codes.ok:
                    self.log.debug(f"Issue {issue_id} deleted successfully")
                    await self.show_notification(_("issues.delete_success"), severity=Severity.SUCCESS, duration=1500)
                    page.update()
                    await self._table.load(reset_page=True)
                else:
                    status_code = response.status_code if response else "no response"
                    self.log.error(f"Delete issue failed: {status_code}")
                    await self.show_notification(_("issues.delete_error"), severity=Severity.ERROR, duration=1500)
                    page.update()
            except Exception as ex:
                self.log.error(f"Delete issue error: {ex}")
                await self.show_notification(_("messages.unexpected_error"), severity=Severity.ERROR)
                page.update()

        self.page.run_task(do_delete)

    def _handle_add_stamp(self, issue_id: int) -> None:
        """Open the StampForm dialog to create a new stamp.

        Args:
            issue_id: The ID of the issue to add a stamp to.
        """
        self.log.debug(f"Add stamp to issue {issue_id}")
        page = self.page

        async def do_show() -> None:
            form = StampForm(
                page=page,
                issue_service=self._issue_service,
                issue_id=issue_id,
                on_success=lambda: page.run_task(self._table.load, reset_page=True),
            )
            await form.show()

        self.page.run_task(do_show)

    async def _handle_add_issue(self, e: ft.ControlEvent) -> None:
        """Open the Add Issue form dialog.

        Shows the IssueForm dialog to create a new stamp issue. On
        successful creation, reloads the issue table.

        Args:
            e: The click event from the add-issue IconButton.
        """
        self.log.debug("Add new issue")
        form = IssueForm(
            page=self.page,
            issue_service=self._issue_service,
            on_success=lambda: self.page.run_task(self._table.load, reset_page=True),
        )
        await form.show()