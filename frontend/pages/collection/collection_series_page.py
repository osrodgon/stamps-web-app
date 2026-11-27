"""The series of one collection, paginated and filtered (plan step B3).

The second screen: from a collection card to its series. It mirrors the admin's
issues table — a name filter, a year range, a sort selector and the shared
paginator — but the rows carry the collection's figures: how many stamps of the series
the user owns, what they paid and what the catalogue says it is worth.

The header summary comes from the overview row (`GET /collections/`), which already
computes the counters; the paid total of the whole collection is not there yet, so the
header shows series and stamps.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from components.buttons.icon_button import IconButton
from components.buttons.link_button import LinkButton
from components.buttons.primary_button import PrimaryButton
from components.collection.issue_progress_card import IssueProgressCard
from components.colors import DARK_BLUE_GREY, GREY_700, ROW_BORDER, SKY_BLUE
from components.constants import (
    CARD_BORDER_RADIUS,
    DEBOUNCE_DELAY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_HEADING,
    FONT_SIZE_XS,
    HEADER_HEIGHT,
    PAGE_PADDING,
    PAGE_SCROLL_GUTTER,
)
from components.form.dialogs.add_stamps_dialog import AddStampsDialog
from components.form.dropdown import Dropdown
from components.form.text_field import TextField
from components.layout.app_drawer import AppDrawer
from components.layout.app_header import AppHeader
from components.table.column_def import fmt_currency, fmt_number
from components.table.table_pagination import TablePagination
from components.templates.standard_page import StandardPage
from core.severity import Severity
from core.translations import _, get_language
from core.urls import URLs
from services.catalogue_service import CatalogueService
from services.collection_item_service import CollectionItemService
from services.collection_service import CollectionService
from settings import (
    USER_EMAIL,
    USER_FIRST_NAME,
    USER_JWT_TOKEN,
    USER_LAST_NAME,
)


class CollectionSeriesPage(StandardPage):
    """The series of one collection.

    Args:
        page: the Flet page.
        collection_id: the collection to show.
        collection_service: injected for tests; built from the stored JWT otherwise.
        item_service: injected for tests; built from the stored JWT otherwise.
        catalogue_service: injected for tests; built from the stored JWT otherwise.
    """

    PAGE_SIZE: int = 15
    DEFAULT_SORT: str = "date_asc"
    #: The sort selector's values and what each means for the API.
    SORT_OPTIONS: dict = {
        "date_asc": ("date", "asc"),
        "date_desc": ("date", "desc"),
        "name": ("name", "asc"),
    }

    def __init__(
        self,
        page: ft.Page,
        collection_id: int,
        collection_service: Optional[CollectionService] = None,
        item_service: Optional[CollectionItemService] = None,
        catalogue_service: Optional[CatalogueService] = None,
    ) -> None:
        super().__init__(page=page, header_height=HEADER_HEIGHT)

        self._collection_id: int = collection_id
        self._collection_service: Optional[CollectionService] = collection_service
        self._item_service: Optional[CollectionItemService] = item_service
        self._catalogue_service: Optional[CatalogueService] = catalogue_service
        self._collection: Optional[dict] = None
        self._lang: str = get_language()

        self._page_number: int = 1
        self._page_size: int = self.PAGE_SIZE
        self._total: int = 0
        self._sort_key: str = self.DEFAULT_SORT
        self._name_filter: str = ""
        self._year_filter: str = ""
        self._name_task: Optional[asyncio.Task] = None
        self._year_task: Optional[asyncio.Task] = None

        self.header = self.set_app_header(AppHeader())
        menu = IconButton(
            icon=ft.Icons.MENU,
            bgcolor=DARK_BLUE_GREY,
            on_click=self.menu_clicked,
        )
        title = ft.Text(
            _("collections.title"),
            color=ft.Colors.WHITE,
            font_family="Roboto-Bold",
            size=20,
        )
        self.header.add_left(menu)
        self.header.add_left(title)

        self.drawer = AppDrawer(on_logout=self.request_logout)

        self._name_text: ft.Text = ft.Text(
            "", size=FONT_SIZE_HEADING, weight=ft.FontWeight.BOLD
        )
        self._summary_text: ft.Text = ft.Text(
            "", size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._crumb_name: ft.Text = ft.Text(
            "",
            size=FONT_SIZE_XS,
            color=DARK_BLUE_GREY,
            weight=ft.FontWeight.BOLD,
        )

        self._name_field: TextField = TextField(
            label=_("collections.filter_series"),
            hint_text=_("collections.filter_name"),
            on_change=self._on_name_change,
            expand=True,
        )
        #: The two year boxes of the mockup. Typed, not dragged: a series may be
        #: catalogued under a year that no other series uses, so nothing limits it.
        self._from_year: TextField = self._year_field(
            "collections.filter_from_year"
        )
        self._to_year: TextField = self._year_field("collections.filter_to_year")
        self._sort: ft.Dropdown = self._build_sort()

        self._loading: ft.ProgressBar = ft.ProgressBar(color=SKY_BLUE, visible=False)
        self._empty_text: ft.Text = ft.Text(
            _("collections.empty_series"), size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._empty_text.visible = False
        self._empty_action: PrimaryButton = PrimaryButton(
            text=_("collections.add_first_stamp"),
            on_click=self._open_add_dialog,
            expand=False,
        )
        self._empty_box: ft.Column = ft.Column(
            controls=[self._empty_text, self._empty_action],
            spacing=8,
            tight=True,
            visible=False,
        )
        self._error_text: ft.Text = ft.Text(
            _("collections.load_failed"), size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._error_box: ft.Column = ft.Column(
            controls=[
                self._error_text,
                PrimaryButton(
                    text=_("collections.retry"),
                    icon=ft.Icons.REFRESH,
                    on_click=self._retry,
                    expand=False,
                ),
            ],
            spacing=8,
            tight=True,
            visible=False,
        )

        #: One card per series, as the mockup draws them, with a gap between.
        self._rows_column: ft.Column = ft.Column(
            controls=[], spacing=10, tight=True
        )
        self._rows_box: ft.Container = ft.Container(
            visible=False, content=self._rows_column
        )
        self._pagination: TablePagination = TablePagination(
            page=1,
            page_size=self._page_size,
            total=0,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_page_size_change,
            page_size_options=[15, 30, 50],
            label=_("pagination.series_per_page"),
        )
        self._pagination.visible = False
        self._pagination.bgcolor = ft.Colors.WHITE
        self._pagination.border = ft.Border.all(1, ROW_BORDER)
        self._pagination.border_radius = CARD_BORDER_RADIUS
        self._pagination.padding = ft.Padding.symmetric(horizontal=16, vertical=10)

        self.content_area = ft.Container(
            expand=True,
            padding=PAGE_PADDING,
            #: A list, not a column: its right padding is the room the floating
            #: scrollbar needs, and a column's children would end under it.
            content=ft.ListView(
                padding=ft.Padding.only(right=PAGE_SCROLL_GUTTER),
                controls=[
                    self._build_breadcrumb(),
                    self._build_header(),
                    self._build_filters(),
                    self._loading,
                    self._error_box,
                    self._empty_box,
                    self._rows_box,
                    self._pagination,
                ],
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=16,
            ),
        )

        self.main.content = ft.Stack(
            controls=[self.content_area, self.drawer],
            expand=True,
        )

        page.run_task(self.read_prefs)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_breadcrumb(self) -> ft.Row:
        """`Collections / <name>`, the first part a way back.

        The link is tight and not underlined, and the name is bold, as the mockup
        draws it: the button's own padding is what made the two gaps around the
        slash differ.
        """
        return ft.Row(
            controls=[
                LinkButton(
                    _("collections.title"),
                    on_click=self._back,
                    underline=False,
                    padding=ft.Padding.all(0),
                ),
                ft.Text("/", size=FONT_SIZE_XS, color=GREY_700),
                self._crumb_name,
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_header(self) -> ft.Row:
        """The collection's name and its figures, as the mockup's head.

        The two share the baseline in the mockup. `BASELINE` alignment is out —
        it needs a `textBaseline` Flet does not send and collapses the page (B4b)
        — so the meta is lifted by a few pixels instead, which is what the eye
        reads as the same line.
        """
        return ft.Row(
            controls=[
                self._name_text,
                ft.Container(
                    content=self._summary_text,
                    padding=ft.Padding.only(bottom=4),
                ),
                ft.Container(expand=True),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

    def _build_filters(self) -> ft.Container:
        """The filters in the mockup's card, with the look the rest of the app has.

        The card is only a frame: the controls are the house text field and dropdown,
        so this screen does not invent a second way of drawing a filter. No `wrap`:
        Flet wraps an `expand` child in an `Expanded`, which is invalid inside a Wrap
        and leaves Flutter painting its error placeholder over the content.
        """
        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ROW_BORDER),
            border_radius=CARD_BORDER_RADIUS,
            padding=ft.Padding.only(left=16, right=16, top=18, bottom=10),
            content=ft.Row(
                controls=[
                    self._name_field,
                    self._from_year,
                    self._to_year,
                    self._sort,
                    ft.Container(expand=True),
                    PrimaryButton(
                        text=_("collections.add_stamps_action"),
                        icon=ft.Icons.ADD,
                        on_click=self._open_add_dialog,
                        expand=False,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _year_field(self, label_key: str) -> TextField:
        """One year box: a number, as wide as four digits and its label."""
        return TextField(
            label=_(label_key),
            on_change=self._on_year_change,
            expand=False,
            width=140,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

    def _build_sort(self) -> Dropdown:
        """The sort selector: date up, date down or name.

        The house dropdown, not `ft.Dropdown`: it wears the same underline and
        the same label as the name and year fields beside it, so the card does not
        put three controls of two shapes on one line.
        """
        return Dropdown(
            label=_("collections.filter_sort"),
            options=[
                ft.dropdown.Option(
                    key="date_asc", text=_("collections.sort_date_asc")
                ),
                ft.dropdown.Option(
                    key="date_desc", text=_("collections.sort_date_desc")
                ),
                ft.dropdown.Option(key="name", text=_("collections.sort_name")),
            ],
            value=self.DEFAULT_SORT,
            width=170,
            expand=False,
            on_change=self._on_sort_change,
        )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    async def read_prefs(self) -> None:
        """Read the session, fill the drawer and load the screen."""
        prefs = ft.SharedPreferences()

        first_name = await prefs.get(USER_FIRST_NAME)
        last_name = await prefs.get(USER_LAST_NAME)
        email = await prefs.get(USER_EMAIL)
        self.drawer.update_data(first_name, last_name, email)

        if self._collection_service is None or self._item_service is None:
            token = await prefs.get(USER_JWT_TOKEN)
            self._collection_service = CollectionService(token or "")
            self._item_service = CollectionItemService(token or "")
        if self._catalogue_service is None:
            token = await prefs.get(USER_JWT_TOKEN)
            self._catalogue_service = CatalogueService(token or "")

        await self.load()

    async def load(self) -> None:
        """Load the collection and its series."""
        await self._load_collection()
        if self._collection is None:
            return
        await self.load_series()

    async def _load_collection(self) -> None:
        """The collection's name and counters, from the overview list."""
        self._loading.visible = True
        self._error_box.visible = False
        self.main_page.update()

        if self._collection_service is None:
            self._loading.visible = False
            self._show_error()
            return

        response = await self._collection_service.get_collections()
        self._loading.visible = False

        if response is None or response.status_code not in (200, 403):
            self._show_error()
            return
        if response.status_code == 403:
            await self._expire_session()
            return

        rows = response.json().get("data") or []
        collection = next(
            (row for row in rows if int(row.get("id", 0)) == self._collection_id),
            None,
        )
        if collection is None:
            await self.show_notification(
                _("collections.load_failed"), Severity.ERROR
            )
            await self.main_page.push_route(URLs.Frontend.collections)
            return

        self._collection = collection
        self._name_text.value = collection.get("name") or ""
        self._summary_text.value = self.summary_label(collection)
        self._crumb_name.value = collection.get("name") or ""
        self.main_page.update()

    async def load_series(self) -> None:
        """Fetch and paint the current page of series."""
        if self._item_service is None:
            self._show_error()
            return

        self._loading.visible = True
        self._error_box.visible = False
        self.main_page.update()

        sort_by, order = self.SORT_OPTIONS[self._sort_key]
        response = await self._item_service.get_series(
            self._collection_id,
            page=self._page_number,
            page_size=self._page_size,
            name=self._name_filter,
            year=self._year_filter,
            sort_by=sort_by,
            order=order,
        )
        self._loading.visible = False

        if response is None or response.status_code not in (200, 403):
            self._show_error()
            return
        if response.status_code == 403:
            await self._expire_session()
            return

        payload = response.json().get("data") or {}
        pagination = payload.get("pagination") or {}
        self._total = int(pagination.get("total") or 0)
        self._page_number = int(pagination.get("page") or self._page_number)
        self._page_size = int(pagination.get("page_size") or self._page_size)
        self._render(payload.get("issues") or [])

    @staticmethod
    def summary_label(collection: dict) -> str:
        """The header's figures: series, stamps and, when known, what it cost.

        `paid` is null when no copy of the collection carries a price, and that is
        not the same as having paid nothing: the part is left out of the sentence.
        """
        lang: str = get_language()
        summary: str = _(
            "collections.summary",
            series=fmt_number(int(collection.get("series") or 0), lang, zero="0"),
            stamps=fmt_number(int(collection.get("stamps") or 0), lang, zero="0"),
        )
        paid = collection.get("paid")
        if paid is None:
            return summary
        return (
            f"{summary} · "
            f"{_('collections.summary_paid', paid=fmt_currency(paid, lang))}"
        )

    def _render(self, rows: list) -> None:
        """Paint the rows, the empty state and the paginator."""
        self._lang = get_language()
        self._rows_column.controls = [
            IssueProgressCard(row, self._lang, on_open=self._open_issue)
            for row in rows
        ]
        self._rows_box.visible = bool(rows)
        self._empty_text.value = (
            _("collections.empty_series")
            if self._name_filter or self._year_filter
            else _("collections.no_series_yet")
        )
        self._empty_text.visible = not rows
        self._empty_box.visible = not rows
        self._pagination.visible = self._total > 0
        self._pagination.update_state(
            page=self._page_number,
            page_size=self._page_size,
            total=self._total,
        )
        self.main_page.update()

    def _show_error(self) -> None:
        """Show the message and the retry button."""
        self._error_box.visible = True
        self._rows_box.visible = False
        self._empty_text.visible = False
        self.main_page.update()

    # ------------------------------------------------------------------
    # Filters and navigation
    # ------------------------------------------------------------------

    async def _on_name_change(self, event: ft.ControlEvent) -> None:
        """Debounce the name filter."""
        if self._name_task is not None:
            self._name_task.cancel()
        self._name_task = asyncio.create_task(
            self._debounced_name(event.control.value)
        )

    async def _debounced_name(self, value: str) -> None:
        """Apply the name filter after the typing stops."""
        await asyncio.sleep(DEBOUNCE_DELAY)
        self._name_filter = (value or "").strip()
        self._page_number = 1
        await self.load_series()

    async def _on_year_change(self, event: ft.ControlEvent) -> None:
        """Debounce the year range while either box is being typed in."""
        if self._year_task is not None:
            self._year_task.cancel()
        self._year_task = asyncio.create_task(self._debounced_year())

    async def _debounced_year(self) -> None:
        """Apply the two boxes after the typing stops."""
        await asyncio.sleep(DEBOUNCE_DELAY)
        self._year_filter = self.year_filter(
            self._from_year.value, self._to_year.value
        )
        self._page_number = 1
        await self.load_series()

    @staticmethod
    def year_filter(from_value: Optional[str], to_value: Optional[str]) -> str:
        """The `year` parameter of the endpoint, from the two boxes.

        `1850`, `1850-1860`, `1850-` and `-1860` are all understood by the API: an
        open end is a bound, not a missing number. What is not a number is dropped,
        so half-typed input asks for nothing instead of asking for the year zero.
        """
        start = CollectionSeriesPage.__year(from_value)
        end = CollectionSeriesPage.__year(to_value)

        if start is not None and end is not None:
            return f"{start}-{end}"
        if start is not None:
            return f"{start}-"
        if end is not None:
            return f"-{end}"
        return ""

    @staticmethod
    def __year(value: Optional[str]) -> Optional[int]:
        """One box as a year, or None when it is empty or not a number."""
        text = (value or "").strip()
        if not text.isdigit():
            return None
        return int(text)

    async def _on_sort_change(self, event: ft.ControlEvent) -> None:
        """Apply the chosen order and go back to the first page."""
        if event.control.value in self.SORT_OPTIONS:
            self._sort_key = event.control.value
        self._page_number = 1
        await self.load_series()

    async def _on_page_change(self, page: int) -> None:
        """Ask for another page."""
        self._page_number = page
        await self.load_series()

    async def _on_page_size_change(self, page_size: int) -> None:
        """Change the page size and go back to the first page."""
        self._page_size = page_size or self.PAGE_SIZE
        self._page_number = 1
        await self.load_series()

    def _open_add_dialog(self, event: Optional[ft.ControlEvent] = None) -> None:
        """Open the catalogue and add stamps from there."""
        if self._catalogue_service is None:
            return

        AddStampsDialog(
            self.main_page,
            self._catalogue_service,
            self._collection_id,
            collection_name=(self._collection or {}).get("name") or "",
            on_added=self._after_add,
            on_forbidden=self._session_expired,
        ).show()

    def _after_add(self, created: int, skipped: int) -> None:
        """Reload the series behind the dialog, so the new ones appear."""
        self._page_number = 1
        self.main_page.run_task(self.load_series)

    def _open_issue(self, issue_id: int) -> None:
        """Open one series of this collection."""
        self.main_page.run_task(self._push_issue, issue_id)

    async def _push_issue(self, issue_id: int) -> None:
        """Navigate to the series' detail."""
        await self.main_page.push_route(
            f"{URLs.Frontend.collections}/{self._collection_id}/issues/{issue_id}"
        )

    def _retry(self, event: ft.ControlEvent) -> None:
        """Load the screen again after an error."""
        self.main_page.run_task(self.load)

    async def _back(self, event: ft.ControlEvent) -> None:
        """Go back to the overview."""
        await self.main_page.push_route(URLs.Frontend.collections)

    def _session_expired(self) -> None:
        """Leave for the login, after a 403."""
        self.main_page.run_task(self._expire_session)

    async def _expire_session(self) -> None:
        """Say why and go to the login."""
        await self.show_notification(
            _("collections.session_expired"), Severity.WARNING
        )
        await self.main_page.push_route(URLs.Frontend.login)

    async def menu_clicked(self, event: ft.ControlEvent) -> None:
        """Open or close the drawer."""
        if self.drawer.offset.x == 0:
            self.drawer.offset = ft.Offset(-1, 0)
        else:
            self.drawer.offset = ft.Offset(0, 0)
        self.drawer.update()
