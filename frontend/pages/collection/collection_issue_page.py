"""One series of a collection, read-only, with the user's copies (plan step B4).

The third screen: the catalogue series as the admin shows it — no edit, no delete —
and under each stamp the block the user can write, "Your copy". The catalogue fields
are text; the API refuses anything but the six fields of the copy, so the screen and
the server agree on what is editable.

The summary is recomputed from the cards after each write: no request and no flicker,
and a refused save leaves the card showing what the server answered.
"""

from __future__ import annotations

from typing import Optional

import flet as ft

from components.buttons.action_icon import ActionIcon
from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.buttons.icon_button import IconButton
from components.buttons.primary_button import PrimaryButton
from components.collection.collection_stamp_card import CollectionStampCard
from components.colors import (
    AMBER_BG,
    AMBER_INK,
    DARK_BLUE_GREY,
    GREY_700,
    SKY_BLUE,
)
from components.constants import (
    CARD_BORDER_RADIUS,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XS,
    HEADER_HEIGHT,
    PAGE_PADDING,
    PAGE_SCROLL_GUTTER,
)
from components.layout.app_drawer import AppDrawer
from components.collection.remove_series_dialog import RemoveSeriesDialog
from components.layout.app_header import AppHeader
from components.layout.header_crumbs import HeaderCrumbs
from core.collection_names import CollectionNames
from components.table.column_def import fmt_currency, fmt_number
from components.table.issue_detail.issue_header_section import IssueHeaderSection
from components.table.issue_detail.issue_specs_grid import IssueSpecsGrid
from components.templates.standard_page import StandardPage
from core.severity import Severity
from core.translations import _, get_language
from core.urls import URLs
from services.collection_item_service import CollectionItemService
from services.collection_service import CollectionService
from settings import (
    USER_EMAIL,
    USER_FIRST_NAME,
    USER_JWT_TOKEN,
    USER_LAST_NAME,
)


class CollectionIssuePage(StandardPage):
    """The series of a collection with the user's copies.

    Args:
        page: the Flet page.
        collection_id: the collection the series belongs to.
        issue_id: the series to show.
        collection_service: injected for tests; built from the stored JWT otherwise.
        item_service: injected for tests; built from the stored JWT otherwise.
    """

    def __init__(
        self,
        page: ft.Page,
        collection_id: int,
        issue_id: int,
        collection_service: Optional[CollectionService] = None,
        item_service: Optional[CollectionItemService] = None,
    ) -> None:
        super().__init__(page=page, header_height=HEADER_HEIGHT)

        self._collection_id: int = collection_id
        self._issue_id: int = issue_id
        self._collection_service: Optional[CollectionService] = collection_service
        self._item_service: Optional[CollectionItemService] = item_service
        self._collection_name: Optional[str] = None
        self._condition_types: list = []
        self._locations: list = []
        self._cards: list[CollectionStampCard] = []
        self._lang: str = get_language()
        #: How many copies of the series the collection holds, for the question.
        self._owned_copies: int = 0
        self.header = self.set_app_header(AppHeader())
        menu = IconButton(
            icon=ft.Icons.MENU,
            bgcolor=DARK_BLUE_GREY,
            on_click=self.menu_clicked,
        )
        #: The path lives in the header (plan D1); the last step is the series.
        self._crumbs: HeaderCrumbs = HeaderCrumbs(
            [
                (_("collections.title"), self._go_collections),
                (
                    CollectionNames.get(collection_id) or "",
                    self._go_collections_parent,
                ),
                ("", None),
            ]
        )
        self.header.add_left(menu)
        # The path takes the middle, which is the space that stretches, so the
        # long names truncate instead of growing the bar.
        self.header.center_area.alignment = ft.MainAxisAlignment.START
        self.header.add_center(self._crumbs)

        self.drawer = AppDrawer(on_logout=self.request_logout)

        #: Where the series sits in the collection's list, and the two arrows.
        self._neighbours: dict = {}
        self._position_text: ft.Text = ft.Text(
            "", size=FONT_SIZE_XS, color=GREY_700
        )
        self._previous_button: ft.IconButton = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip=_("collections.previous_series"),
            on_click=self._go_previous,
        )
        self._next_button: ft.IconButton = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip=_("collections.next_series"),
            on_click=self._go_next,
        )
        self._remove_button: ActionIcon = ActionIcon(
            icon=ft.Icons.DELETE,
            tooltip=_("collections.remove_series"),
            hover_color=ft.Colors.RED_700,
            on_click=self._ask_remove_series,
        )
        self._loading: ft.ProgressBar = ft.ProgressBar(color=SKY_BLUE, visible=False)
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
        self._empty_text: ft.Text = ft.Text(
            _("collections.empty_stamps"), size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._empty_text.visible = False
        self._summary_text: ft.Text = ft.Text(
            "", size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._cards_row: ft.ResponsiveRow = ft.ResponsiveRow(
            controls=[], spacing=16, run_spacing=16
        )
        self._detail_box: ft.Column = ft.Column(
            controls=[], spacing=12, visible=False
        )

        self.content_area = ft.Container(
            expand=True,
            padding=PAGE_PADDING,
            #: A list, not a column: its right padding is the room the floating
            #: scrollbar needs, and a column's children would end under it.
            content=ft.ListView(
                padding=ft.Padding.only(right=PAGE_SCROLL_GUTTER),
                controls=[
                    self._loading,
                    self._error_box,
                    self._detail_box,
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

    def _badge(self) -> ft.Container:
        """Says the catalogue half is read-only."""
        return ft.Container(
            content=ft.Text(
                _("collections.catalogue_readonly"),
                size=FONT_SIZE_XS,
                color=AMBER_INK,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=AMBER_BG,
            border_radius=CARD_BORDER_RADIUS,
        )

    def _stamps_head(self) -> ft.Container:
        """`Stamps` and the summary, as the mockup's section head.

        The alignment is `CENTER` on purpose: `BASELINE` needs a `textBaseline`
        that Flet does not send, and Flutter reacts by collapsing the page and
        painting the content offset upwards, with nothing in the log.
        """
        return ft.Container(
            margin=ft.Margin.only(top=14),
            content=ft.Row(
                controls=[
                    ft.Text(
                        _("collections.stamps_section"),
                        size=FONT_SIZE_SMALL_HEADING,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self._summary_text,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
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

        await self.load()

    async def load(self) -> None:
        """Load the collection's name, the references and the series."""
        await self._load_collection_name()
        if self._collection_name is None:
            return
        await self._load_references()
        await self._load_detail()

    async def _load_collection_name(self) -> None:
        """The collection's name, from the cache or from the overview list.

        Moving between series rebuilds this screen, and the name never changes: when
        it is known, asking for it again is a request that only repaints the same
        text a moment later.
        """
        remembered = CollectionNames.get(self._collection_id)
        if remembered:
            self._collection_name = remembered
            self._crumbs.set_text(1, remembered)
            return

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
        row = next(
            (item for item in rows if int(item.get("id", 0)) == self._collection_id),
            None,
        )
        if row is None:
            await self.show_notification(
                _("collections.load_failed"), Severity.ERROR
            )
            await self.main_page.push_route(URLs.Frontend.collections)
            return

        self._collection_name = row.get("name") or ""
        CollectionNames.remember(self._collection_id, self._collection_name)
        self._crumbs.set_text(1, self._collection_name)
        self.main_page.update()

    async def _load_references(self) -> None:
        """The conditions and locations the two selects offer."""
        if self._item_service is None:
            return

        conditions = await self._item_service.get_condition_types()
        if conditions is not None and conditions.status_code == 200:
            self._condition_types = conditions.json().get("data") or []

        locations = await self._item_service.get_locations()
        if locations is not None and locations.status_code == 200:
            self._locations = locations.json().get("data") or []

    async def _load_detail(self) -> None:
        """Fetch and paint the series with its stamps."""
        if self._item_service is None:
            self._show_error()
            return

        self._loading.visible = True
        self._error_box.visible = False
        self.main_page.update()

        response = await self._item_service.get_issue(
            self._collection_id, self._issue_id
        )
        self._loading.visible = False

        if response is None or response.status_code not in (200, 403, 404):
            self._show_error()
            return
        if response.status_code == 403:
            await self._expire_session()
            return
        if response.status_code == 404:
            await self.main_page.push_route(
                f"{URLs.Frontend.collections}/{self._collection_id}"
            )
            return

        self._render(response.json().get("data") or {})

    def _render(self, detail: dict) -> None:
        """Paint the read-only series and its stamp cards."""
        issue = detail.get("issue") or {}
        stamps = detail.get("stamps") or []
        summary = detail.get("summary") or {}
        self._lang = get_language()

        self._crumbs.set_text(2, issue.get("name") or "")
        self._owned_copies = int(summary.get("owned") or 0)
        self._neighbours = detail.get("neighbours") or {}
        self.__paint_neighbours()
        self._summary_text.value = self.summary_label(
            int(summary.get("owned") or 0),
            int(summary.get("total") or 0),
            summary.get("paid"),
            self._lang,
        )

        self._cards = [
            self._card(stamp, issue) for stamp in stamps
        ]
        self._cards_row.controls = self._cards
        self._empty_text.visible = not stamps
        self._detail_box.controls = [
            IssueHeaderSection(
                issue,
                self._lang,
                hide_action_icons=True,
                trailing=[
                    self._previous_button,
                    self._position_text,
                    self._next_button,
                    self._remove_button,
                    ft.Container(width=4),
                ],
                subtitle_trailing=[self._badge()],
            ),
            IssueSpecsGrid(issue),
            self._stamps_head(),
            self._empty_text,
            self._cards_row,
        ]
        self._detail_box.visible = True
        self.main_page.update()

    def _card(self, stamp: dict, issue: dict) -> CollectionStampCard:
        """One stamp card, with the issue's year for the picture's path.

        The cards sit two per row from `lg` (the mockup's 980px breakpoint) and
        one per row below it. `col` is the only thing the grid needs; the card
        itself carries no width.
        """
        prepared = dict(stamp, issue_year=issue.get("year"))
        card = CollectionStampCard(
            self.main_page,
            prepared,
            self._lang,
            condition_types=self._condition_types,
            locations=self._locations,
            on_save=self._save_item,
            on_add=self._add_item,
            on_remove=self._remove_item,
            on_changed=self._refresh_summary,
        )
        card.col = {
            ft.ResponsiveRowBreakpoint.XS: 12,
            ft.ResponsiveRowBreakpoint.LG: 6,
        }
        return card

    @staticmethod
    def summary_label(owned: int, total: int, paid, lang: str) -> str:
        """`3 of 5 stamps · Paid €315.00`, from the locale keys."""
        progress = _(
            "collections.progress",
            owned=fmt_number(owned, lang, zero="0"),
            total=fmt_number(total, lang, zero="0"),
        )
        return f"{progress} · {_('collections.paid')}: {fmt_currency(paid, lang)}"

    def __paint_neighbours(self) -> None:
        """Enable the arrows the list allows and write `3 / 14` between them."""
        if not self._neighbours:
            self._position_text.value = ""
            self._previous_button.visible = False
            self._next_button.visible = False
            return

        self._position_text.value = _(
            "collections.position_of",
            position=fmt_number(
                int(self._neighbours.get("position") or 0), self._lang, zero="0"
            ),
            total=fmt_number(
                int(self._neighbours.get("total") or 0), self._lang, zero="0"
            ),
        )
        self._previous_button.visible = True
        self._next_button.visible = True
        self._previous_button.disabled = self._neighbours.get("previous") is None
        self._next_button.disabled = self._neighbours.get("next") is None

    def _go_previous(self, event: ft.ControlEvent) -> None:
        """Open the series before this one in the collection's list."""
        previous = self._neighbours.get("previous")
        if previous is not None:
            self.main_page.run_task(self.__push_series, int(previous))

    def _go_next(self, event: ft.ControlEvent) -> None:
        """Open the series after this one in the collection's list."""
        following = self._neighbours.get("next")
        if following is not None:
            self.main_page.run_task(self.__push_series, int(following))

    async def __push_series(self, issue_id: int) -> None:
        """Navigate to another series of the same collection."""
        await self.main_page.push_route(
            f"{URLs.Frontend.collections}/{self._collection_id}/issues/{issue_id}"
        )

    def _refresh_summary(self) -> None:
        """Recompute the summary from the cards, after a write."""
        owned = sum(1 for card in self._cards if card.item is not None)
        prices = [
            float(card.item.get("price_paid"))
            for card in self._cards
            if card.item is not None and card.item.get("price_paid") is not None
        ]
        paid = sum(prices) if prices else None
        self._summary_text.value = self.summary_label(
            owned, len(self._cards), paid, self._lang
        )
        self.main_page.update()

    def _ask_remove_series(self, event: ft.ControlEvent = None) -> None:
        """Ask once before the series leaves the collection."""
        if self._item_service is None:
            return
        RemoveSeriesDialog(
            self.main_page,
            self._item_service,
            self._collection_id,
            self._issue_id,
            name=self._crumbs.text(2),
            count=self._owned_copies,
            on_removed=self._after_remove,
            on_forbidden=self._session_expired,
        ).show()

    def _after_remove(self, deleted: int) -> None:
        """Say what left and go back to the collection's list."""
        self.main_page.run_task(self._say_removed, deleted)

    async def _say_removed(self, deleted: int) -> None:
        await self.show_notification(
            _("collections.series_removed", count=deleted), Severity.SUCCESS
        )
        await self.main_page.push_route(
            f"{URLs.Frontend.collections}/{self._collection_id}"
        )

    def _show_error(self) -> None:
        """Show the message and the retry button."""
        self._error_box.visible = True
        self._detail_box.visible = False
        self._empty_text.visible = False
        self.main_page.update()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def _save_item(
        self, stamp: dict, item_id: int, payload: dict
    ) -> Optional[dict]:
        """Save the six fields and return what the API wrote."""
        if self._item_service is None:
            return None
        response = await self._item_service.update_item(item_id, payload)

        if response is None or response.status_code not in (200, 403):
            await self.show_notification(
                _("collections.save_failed"), Severity.ERROR
            )
            return None
        if response.status_code == 403:
            await self._expire_session()
            return None
        return response.json().get("data")

    async def _add_item(self, stamp: dict) -> Optional[dict]:
        """Add the user's copy of one stamp."""
        if self._item_service is None:
            return None
        response = await self._item_service.add_item(
            self._collection_id, int(stamp.get("id") or 0)
        )

        if response is None:
            await self.show_notification(
                _("collections.save_failed"), Severity.ERROR
            )
            return None
        if response.status_code == 403:
            await self._expire_session()
            return None
        if response.status_code == 409:
            # The page was stale: load the series again and show the copy.
            await self._load_detail()
            return None
        if response.status_code != 201:
            await self.show_notification(
                _("collections.save_failed"), Severity.ERROR
            )
            return None
        return response.json().get("data")

    async def _remove_item(self, item_id: int) -> bool:
        """Remove the copy; True when the API deleted it."""
        if self._item_service is None:
            return False
        response = await self._item_service.delete_item(item_id)

        if response is None or response.status_code not in (200, 403):
            await self.show_notification(
                _("collections.delete_failed"), Severity.ERROR
            )
            return False
        if response.status_code == 403:
            await self._expire_session()
            return False
        return True

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def _go_collections(self, event: ft.ControlEvent) -> None:
        """Back to the overview."""
        await self.main_page.push_route(URLs.Frontend.collections)

    async def _go_collections_parent(self, event: ft.ControlEvent) -> None:
        """Back to this collection's series."""
        await self.main_page.push_route(
            f"{URLs.Frontend.collections}/{self._collection_id}"
        )

    def _retry(self, event: ft.ControlEvent) -> None:
        """Load the screen again after an error."""
        self.main_page.run_task(self.load)

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
