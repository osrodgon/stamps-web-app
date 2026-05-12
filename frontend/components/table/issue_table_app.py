"""
Main issue table component.

Assembles TableHeader, IssueRow, and TablePagination into a full-featured
data table with server-side sorting and pagination.
"""

from typing import Optional

import flet as ft

from components.colors import EXPANSION_BG, HEADER_BG, ICON_GREY, ROW_BORDER
from components.table.column_def import COLUMNS
from components.table.issue_row import IssueRow
from components.table.table_header import TableHeader
from components.table.table_pagination import TablePagination
from core.translations import _, get_language
from services.stamp_issue_service import StampIssueService


class IssueTableApp(ft.Container):
    """Main issue table with header, rows, and pagination.

    Manages state for pagination and sorting, fetches data from the
    backend API, and coordinates all sub-components.
    """

    def __init__(self, service: Optional[StampIssueService] = None) -> None:
        super().__init__()
        self._service: StampIssueService = service or StampIssueService()
        self.expand = True

        self._data: list[dict] = []
        self._total: int = 0
        self._current_page: int = 1
        self._rows_per_page: int = 15
        self._sort_key: str = "date"
        self._sort_order: str = "asc"
        self._lang: str = get_language()

        self._progress_bar: ft.ProgressBar = ft.ProgressBar(
            visible=False,
            color=HEADER_BG,
            bgcolor=EXPANSION_BG,
        )
        self._rows_container: ft.Column = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self._empty_text: ft.Text = ft.Text(
            _("collections.no_issues_found"),
            visible=False,
            size=14,
            font_family="Roboto-Bold",
            color=ICON_GREY,
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
                    content=ft.Column(
                        controls=[self._rows_container],
                        scroll=ft.ScrollMode.ADAPTIVE,
                        spacing=0,
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

    async def load(self) -> None:
        """Fetch data from the API and update all sub-components."""
        self._progress_bar.visible = True
        self._lang = get_language()
        self.update()

        response = await self._service.get_issues(
            page=self._current_page,
            page_size=self._rows_per_page,
            sort_by=self._sort_key,
            order=self._sort_order,
        )

        if response and response.status_code == 200:
            body: dict = response.json()
            self._data = body.get("data").get("issues", [])
            pagination: dict = body.get("data").get("pagination", {})
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

    def _rebuild_rows(self) -> None:
        """Replace all IssueRow instances with current data."""
        self._rows_container.controls.clear()

        if not self._data:
            self._empty_text.visible = True
            self.update()
            return

        self._empty_text.visible = False
        for index, issue in enumerate(self._data):
            row: IssueRow = IssueRow(
                issue=issue,
                row_index=index,
                columns=COLUMNS,
                lang=self._lang,
                on_expand=self._on_expand,
            )
            self._rows_container.controls.append(row)
        self.update()

    def _on_sort(self, sort_key: str, sort_order: str) -> None:
        """Handle sort change from TableHeader."""
        self._sort_key = sort_key
        self._sort_order = sort_order
        self._current_page = 1
        self._schedule_fetch()

    def _on_page_change(self, page: int) -> None:
        """Handle page navigation from TablePagination."""
        self._current_page = page
        self._schedule_fetch()

    def _on_page_size_change(self, page_size: int) -> None:
        """Handle page size change from TablePagination."""
        self._rows_per_page = page_size
        self._current_page = 1
        self._schedule_fetch()

    def _on_expand(self, issue_id: int) -> None:
        """Handle row expansion. Placeholder for future stamp fetch."""

    def _schedule_fetch(self) -> None:
        """Refresh data after a state change."""
        self.page.run_task(self.load)
