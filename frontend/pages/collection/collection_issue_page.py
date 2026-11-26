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

from components.buttons.icon_button import IconButton
from components.buttons.link_button import LinkButton
from components.buttons.primary_button import PrimaryButton
from components.collection.collection_stamp_card import CollectionStampCard
from components.colors import (
    BG_ALT,
    DARK_BLUE_GREY,
    GREY_700,
    SKY_BLUE,
)
from components.constants import (
    CARD_BORDER_RADIUS,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_XS,
    HEADER_HEIGHT,
    PAGE_PADDING,
)
from components.layout.app_drawer import AppDrawer
from components.layout.app_header import AppHeader
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

        self._collection_link: LinkButton = LinkButton(
            "", on_click=self._go_collections_parent
        )
        self._series_crumb: ft.Text = ft.Text(
            "", size=FONT_SIZE_XS, color=GREY_700
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
        self._cards_column: ft.Column = ft.Column(controls=[], spacing=12)
        self._detail_box: ft.Column = ft.Column(
            controls=[], spacing=12, visible=False
        )

        self.content_area = ft.Container(
            expand=True,
            padding=PAGE_PADDING,
            content=ft.Column(
                controls=[
                    self._build_breadcrumb(),
                    self._loading,
                    self._error_box,
                    self._empty_text,
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

    def _build_breadcrumb(self) -> ft.Row:
        """`Collections / <collection> / <series>`, the first two links."""
        return ft.Row(
            controls=[
                LinkButton(_("collections.title"), on_click=self._go_collections),
                ft.Text("/", size=FONT_SIZE_XS, color=GREY_700),
                self._collection_link,
                ft.Text("/", size=FONT_SIZE_XS, color=GREY_700),
                self._series_crumb,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _badge(self) -> ft.Container:
        """Says the catalogue half is read-only."""
        return ft.Container(
            content=ft.Text(
                _("collections.catalogue_readonly"),
                size=FONT_SIZE_XS,
                color=GREY_700,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=BG_ALT,
            border_radius=CARD_BORDER_RADIUS,
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
        """The collection's name from the overview list."""
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
        self._collection_link.content.value = self._collection_name
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

        self._series_crumb.value = issue.get("name") or ""
        self._summary_text.value = self.summary_label(
            int(summary.get("owned") or 0),
            int(summary.get("total") or 0),
            summary.get("paid"),
            self._lang,
        )

        self._cards = [
            self._card(stamp, issue) for stamp in stamps
        ]
        self._cards_column.controls = self._cards
        self._empty_text.visible = not stamps
        self._detail_box.controls = [
            ft.Row(
                controls=[self._badge()],
                alignment=ft.MainAxisAlignment.END,
            ),
            IssueHeaderSection(issue, self._lang, hide_action_icons=True),
            IssueSpecsGrid(issue),
            self._summary_text,
            self._cards_column,
        ]
        self._detail_box.visible = True
        self.main_page.update()

    def _card(self, stamp: dict, issue: dict) -> CollectionStampCard:
        """One stamp card, with the issue's year for the picture's path."""
        prepared = dict(stamp, issue_year=issue.get("year"))
        return CollectionStampCard(
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

    @staticmethod
    def summary_label(owned: int, total: int, paid, lang: str) -> str:
        """`3 of 5 stamps · Paid €315.00`, from the locale keys."""
        progress = _(
            "collections.progress",
            owned=fmt_number(owned, lang, zero="0"),
            total=fmt_number(total, lang, zero="0"),
        )
        return f"{progress} · {_('collections.paid')}: {fmt_currency(paid, lang)}"

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
