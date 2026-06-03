"""
Main issue table component.

Assembles TableHeader, IssueRow, and TablePagination into a full-featured
data table with server-side sorting and pagination. Coordinates data fetching
from the backend API, manages filter state (name, year range), and handles
row expansion with async stamp loading. Pagination is automatically reset
to page 1 when filters or sort order change.
"""

from typing import Callable, Optional

import flet as ft
import requests

from components.colors import HEADER_BG, ICON_GREY, ROW_BORDER, SKY_BLUE
from components.table.column_def import COLUMNS
from components.table.issue_row import IssueRow
from components.table.table_header import TableHeader
from components.table.table_pagination import TablePagination
from core.translations import _, get_language
from services.issue_service import IssueService
from components.constants import ICON_SIZE_LARGE, FONT_SIZE_XLARGE


class IssueTableApp(ft.Container):
    """Main issue table with header, rows, and pagination.

    Manages state for pagination, sorting, and filtering. Fetches data
    from the backend API via IssueService and coordinates all sub-components.
    Supports column definitions via the COLUMNS list, name/year text filtering,
    optional year range slider filtering, and server-side pagination/sorting.

    Public methods:
        load(search, reset_page): Fetch data with optional name/year filter.
        set_year_filter(): Apply a year range from an external slider.
    """

    def __init__(
        self,
        service: Optional[IssueService] = None,
        on_edit_stamp: Optional[Callable[[int], None]] = None,
        on_delete_stamp: Optional[Callable[[int, int], None]] = None,
        on_edit_issue: Optional[Callable[[int], None]] = None,
        on_delete_issue: Optional[Callable[[int], None]] = None,
        on_add_stamp: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Initialize the table with sub-components, state, and default layout.

        Sets up internal state for pagination, sorting, and filtering.
        Builds the layout stack: progress bar overlay, scrollable rows
        container, and pagination footer. Initializes the year range
        filter used by the external YearRangeSelector widget.

        Args:
            service: IssueService instance for API communication. Creates
                a new instance if not provided.
            on_edit_stamp: Called with stamp ID when a stamp edit icon is clicked.
            on_delete_stamp: Called with (stamp_id, issue_id) when a stamp delete icon is clicked.
            on_edit_issue: Called with issue ID when the issue edit icon is clicked.
            on_delete_issue: Called with issue ID when the issue delete icon is clicked.
            on_add_stamp: Called with issue ID when the add-stamp button is clicked.
        """
        super().__init__()
        self._service: IssueService = service or IssueService()
        self.expand = True

        self._data: list[dict] = []
        self._total: int = 0
        self._current_page: int = 1
        self._rows_per_page: int = 15
        self._sort_key: str = "date"
        self._sort_order: str = "asc"
        self._name_filter: str = ""
        self._lang: str = get_language()
        self._year_filter: str = ""
        self._on_edit_stamp: Optional[Callable[[int], None]] = on_edit_stamp
        self._on_delete_stamp: Optional[Callable[[int, int], None]] = on_delete_stamp
        self._on_edit_issue: Optional[Callable[[int], None]] = on_edit_issue
        self._on_delete_issue: Optional[Callable[[int], None]] = on_delete_issue
        self._on_add_stamp: Optional[Callable[[int], None]] = on_add_stamp

        self._progress_bar: ft.ProgressBar = ft.ProgressBar(
            visible=False,
            color=HEADER_BG,
            bgcolor=SKY_BLUE,
        )
        self._rows_container: ft.Column = ft.Column(spacing=0, expand=True)
        self._empty_state: ft.Container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=ICON_SIZE_LARGE, color=ICON_GREY),
                            ft.Text(
                                _("collections.no_issues_found"),
                                size=FONT_SIZE_XLARGE,
                                color=ICON_GREY,
                                font_family="Roboto-Bold",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            visible=False,
            expand=True,
        )
        self._table_header: TableHeader = TableHeader(
            columns=COLUMNS,
            sort_key=self._sort_key,
            sort_order=self._sort_order,
            on_sort=self._on_sort,
        )
        self._pagination: TablePagination = TablePagination(
            page=self._current_page,
            page_size=self._rows_per_page,
            total=self._total,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_page_size_change,
        )

        self.border = ft.Border.all(1, ROW_BORDER)
        self.border_radius = 0
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.content = ft.Column(
            controls=[
                ft.Stack(
                    controls=[
                        self._table_header,
                        ft.Container(
                            content=self._progress_bar,
                            left=0,
                            right=0,
                            top=0,
                            height=4,
                        ),
                    ],
                ),
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            ft.Column(
                                controls=[self._rows_container],
                                scroll=ft.ScrollMode.ADAPTIVE,
                                spacing=0,
                                expand=True,
                            ),
                            self._empty_state,
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
                self._pagination,
            ],
            spacing=0,
            expand=True,
        )
        self.bgcolor = ft.Colors.WHITE

    async def load(self, search: str = "", reset_page: bool = False) -> None:
        """Fetch data from the API and update all sub-components.

        Parses the search value via _parse_filter() to resolve name
        vs. year filtering. If no year is extracted from the search
        string, falls back to the active year range filter set by
        set_year_filter() (e.g. from the YearRangeSelector widget).

        When reset_page is True, pagination is reset to page 1 before
        fetching, preventing empty result screens when filters reduce
        the total number of available pages.

        Args:
            search: Raw filter string from the text field. May be a name,
                a year number (e.g. "2002"), or a year pattern (e.g. "19*").
            reset_page: If True, reset to page 1 before fetching.
        """
        if reset_page:
            self._current_page = 1
        self._name_filter = search
        name_val, year_val = self._parse_filter(search)
        if not year_val and self._year_filter:
            year_val = self._year_filter
            
        self._progress_bar.visible = True
        self._lang = get_language()
        self.update()

        response = await self._service.get_issues(
            page=self._current_page,
            page_size=self._rows_per_page,
            sort_by=self._sort_key,
            order=self._sort_order,
            name=name_val,
            year=year_val
        )

        if response and response.status_code == requests.codes.ok:
            body: dict = response.json()
            data_payload = body.get("data") or {}
            self._data = data_payload.get("issues", [])
            pagination: dict = data_payload.get("pagination", {})
            self._total = pagination.get("total", 0)
            self._current_page = pagination.get("page", self._current_page)
            self._rows_per_page = pagination.get("page_size", self._rows_per_page)
            self._sort_key = pagination.get("sort_by", self._sort_key)
            self._sort_order = pagination.get("order", self._sort_order)
        else:
            self._data = []
            self._total = 0

        self._progress_bar.visible = False
        self._rebuild_rows()
        self._pagination.update_state(
            page=self._current_page,
            page_size=self._rows_per_page,
            total=self._total,
        )
        self._table_header.update_sort_indicators(self._sort_key, self._sort_order)
        
    def set_year_filter(self, year_range: str) -> None:
        """Set an active year range filter and reload the table.

        Resets pagination to page 1 before fetching to avoid empty
        result pages when the filtered dataset is smaller.

        Args:
            year_range: Year range string, e.g. "1840-2025". Empty
                string clears the filter.
        """
        self._year_filter = year_range
        self._current_page = 1
        self._schedule_fetch()

    def _rebuild_rows(self) -> None:
        """Replace all IssueRow instances in the rows container with current data.

        Clears existing rows, creates new IssueRow widgets from the loaded
        data, and auto-expands the first row when rows_per_page equals 1.
        Shows the empty state message if no data is available.
        """
        self._rows_container.controls.clear()

        if not self._data:
            self._empty_state.visible = True
            self.update()
            return

        self._empty_state.visible = False
        
        for index, issue in enumerate(self._data):
            auto_expand: bool = index == 0 and self._rows_per_page == 1
            row: IssueRow = IssueRow(
                issue=issue,
                row_index=index,
                columns=COLUMNS,
                lang=self._lang,
                on_expand=self._on_expand,
                expanded=auto_expand,
                service=self._service,
                on_edit_stamp=self._on_edit_stamp,
                on_delete_stamp=self._on_delete_stamp,
                on_edit_issue=self._on_edit_issue,
                on_delete_issue=self._on_delete_issue,
                on_add_stamp=self._on_add_stamp,
            )
            self._rows_container.controls.append(row)
            if auto_expand and issue.get("id") is not None:
                row.set_loading()
                self._on_expand(issue["id"])
        self.update()

    def _on_sort(self, sort_key: str, sort_order: str) -> None:
        """Handle sort change from TableHeader.

        Updates the sort key and order, resets pagination to page 1,
        and triggers a data reload.

        Args:
            sort_key: The column field to sort by.
            sort_order: Sort direction, "asc" or "desc".
        """
        self._sort_key = sort_key
        self._sort_order = sort_order
        self._current_page = 1
        self._schedule_fetch()

    def _on_page_change(self, page: int) -> None:
        """Handle page navigation from TablePagination.

        Args:
            page: The target page number (1-indexed).
        """
        self._current_page = page
        self._schedule_fetch()

    def _on_page_size_change(self, page_size: int) -> None:
        """Handle page size change from TablePagination.

        Resets pagination to page 1 since the total number of pages
        changes when the page size is modified.

        Args:
            page_size: Number of rows to display per page.
        """
        self._rows_per_page = page_size
        self._current_page = 1
        self._schedule_fetch()

    def _on_expand(self, issue_id: int) -> None:
        """Initiate async stamp fetch for the expanded issue row.

        Schedules _fetch_stamps_for_row to run as a background task
        on the page's event loop.

        Args:
            issue_id: The ID of the issue whose stamps should be fetched.
        """
        self.page.run_task(self._fetch_stamps_for_row, issue_id)

    async def _fetch_stamps_for_row(self, issue_id: int) -> None:
        """Fetch stamps from the API and update the expanded IssueRow.

        Searches the rows container for the matching IssueRow by ID
        and calls set_stamps() to rebuild the detail card with the
        fetched stamp data.

        Args:
            issue_id: The ID of the issue whose stamps were fetched.
        """
        response = await self._service.get_issue_stamps(issue_id)
        stamps: list[dict] = response.json() if response and response.ok else []
        for ctrl in self._rows_container.controls:
            if isinstance(ctrl, IssueRow) and ctrl._issue.get("id") == issue_id:
                ctrl.set_stamps(stamps)
                break

    def _schedule_fetch(self) -> None:
        """Schedule an asynchronous data reload after a state change.

        Triggers load() via page.run_task() to fetch fresh data with
        the current filter, sort, and pagination settings.
        """
        self.page.run_task(self.load, search=self._name_filter)
        
    @staticmethod
    def _parse_filter(value: str) -> tuple[str, str]:
        """Parse filter input into name and year query params.

        Conversion rules:
            - Empty input → ("", "")
            - Plain digits (e.g. "2002") → ("", "2002") — single year
            - Digit pattern N* (e.g. "19*") → ("", "1900-1999") — year range
            - Digit pattern NN* (e.g. "200*") → ("", "2000-2009") — year range
            - Everything else (e.g. "Marianne") → ("Marianne", "") — name search

        Returns:
            Tuple of (name_value, year_value) for the API call.
        """
        stripped = value.strip()
        if not stripped:
            return ("", "")

        # nnn* or nn* → year range
        if stripped.endswith("*"):
            digits = stripped[:-1].strip()
            if digits.isdigit():
                d = len(digits)
                z = 4 - d
                start = digits + "0" * z
                end = digits + "9" * z
                return ("", f"{start}-{end}")

        # Plain number → year
        if stripped.isdigit():
            return ("", stripped)

        # Everything else → name
        return (stripped, "")
