"""The collections overview: the user's collections as cards (plan step A5).

This is the first screen a normal user sees after logging in. It loads the list from
`CollectionService` with the JWT of the session, paints one `CollectionCard` per
collection and lets the user create, rename and delete.

It is also where the session is noticed: these endpoints answer 403 when the token
is no longer valid, and the page sends the user to the login instead of showing an
empty grid as if the account had no collections.
"""

from __future__ import annotations

from typing import Optional

import flet as ft

from components.buttons.icon_button import IconButton
from components.buttons.primary_button import PrimaryButton
from components.collection.collection_card import CollectionCard
from components.colors import DARK_BLUE_GREY, GREY_700, ROW_BORDER, SKY_BLUE
from components.constants import (
    CARD_BORDER_RADIUS,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_HEADING,
    FONT_SIZE_SMALL_HEADING,
    HEADER_HEIGHT,
    ICON_SIZE_LARGE,
    PAGE_PADDING,
)
from components.form.dialogs.collection_form import (
    CollectionDeleteDialog,
    CollectionForm,
)
from components.layout.app_drawer import AppDrawer
from components.layout.app_header import AppHeader
from components.layout.header_crumbs import HeaderCrumbs
from core.collection_names import CollectionNames
from components.templates.standard_page import StandardPage
from core.severity import Severity
from core.translations import _, get_language
from core.urls import URLs
from services.collection_service import CollectionService
from settings import (
    USER_EMAIL,
    USER_FIRST_NAME,
    USER_JWT_TOKEN,
    USER_LAST_NAME,
)


class CollectionsPage(StandardPage):
    """The collections overview.

    Args:
        page: the Flet page.
        service: the collections service, or None to build it from the stored JWT
            once the page has read its preferences (the normal path).
    """

    #: One, two or three cards per row.
    GRID_COLUMNS: dict = {"sm": 12, "md": 6, "lg": 4}
    GRID_SPACING: int = 20

    def __init__(
        self, page: ft.Page, service: Optional[CollectionService] = None
    ) -> None:
        super().__init__(page=page, header_height=HEADER_HEIGHT)

        self._service: Optional[CollectionService] = service
        self._collections: list[dict] = []
        self._lang: str = get_language()

        self.header = self.set_app_header(AppHeader())
        menu = IconButton(
            icon=ft.Icons.MENU,
            bgcolor=DARK_BLUE_GREY,
            on_click=self.menu_clicked,
        )
        #: The root of the path, in the same place the deeper screens use it.
        self._crumbs: HeaderCrumbs = HeaderCrumbs([(_("collections.title"), None)])
        self.header.add_left(menu)
        self.header.center_area.alignment = ft.MainAxisAlignment.START
        self.header.add_center(self._crumbs)
        # The action lives in the header, as the admin's "add issue" does.
        self.header.add_right(
            IconButton(
                icon=ft.Icons.ADD,
                bgcolor=DARK_BLUE_GREY,
                on_click=self._handle_new,
                tooltip=_("collections.new"),
            )
        )

        self.drawer = AppDrawer(on_logout=self.request_logout)

        self._count: ft.Text = ft.Text("", size=FONT_SIZE_DEFAULT, color=GREY_700)
        self._loading: ft.ProgressBar = ft.ProgressBar(
            color=SKY_BLUE, visible=False
        )
        self._empty: ft.Container = self._build_empty_state()
        self._grid: ft.ResponsiveRow = ft.ResponsiveRow(
            controls=[],
            spacing=self.GRID_SPACING,
            run_spacing=self.GRID_SPACING,
            visible=False,
        )

        self.content_area = ft.Container(
            expand=True,
            padding=PAGE_PADDING,
            content=ft.Column(
                controls=[
                    self._build_toolbar(),
                    self._loading,
                    self._empty,
                    self._grid,
                ],
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=self.GRID_SPACING,
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

    def _build_toolbar(self) -> ft.Row:
        """How many collections there are; title and action live in the header."""
        return ft.Row(
            controls=[self._count, ft.Container(expand=True)],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

    def _build_empty_state(self) -> ft.Container:
        """What a user with no collections sees, with the one action that helps."""
        return ft.Container(
            visible=False,
            alignment=ft.Alignment.CENTER,
            padding=PAGE_PADDING,
            border=ft.Border.all(1, ROW_BORDER),
            border_radius=CARD_BORDER_RADIUS,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.COLLECTIONS_OUTLINED,
                        size=ICON_SIZE_LARGE,
                        color=GREY_700,
                    ),
                    ft.Text(
                        _("collections.empty_title"),
                        size=FONT_SIZE_SMALL_HEADING,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        _("collections.empty_hint"),
                        size=FONT_SIZE_DEFAULT,
                        color=GREY_700,
                    ),
                    PrimaryButton(
                        text=_("collections.new"),
                        icon=ft.Icons.ADD,
                        on_click=self._handle_new,
                        expand=False,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                tight=True,
            ),
        )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    async def read_prefs(self) -> None:
        """Read the session from the preferences, fill the drawer and load."""
        prefs = ft.SharedPreferences()

        first_name = await prefs.get(USER_FIRST_NAME)
        last_name = await prefs.get(USER_LAST_NAME)
        email = await prefs.get(USER_EMAIL)
        self.drawer.update_data(first_name, last_name, email)

        if self._service is None:
            token = await prefs.get(USER_JWT_TOKEN)
            self._service = CollectionService(token or "")

        await self.load_collections()

    async def load_collections(self) -> None:
        """Fetch the caller's collections and paint them."""
        self._loading.visible = True
        self._grid.visible = False
        self._empty.visible = False
        self.main_page.update()

        if self._service is None:
            await self._expire_session()
            return

        response = await self._service.get_collections()
        self._loading.visible = False

        if response is None or response.status_code not in (200, 403):
            self._grid.visible = False
            self._empty.visible = False
            await self.show_notification(
                _("collections.load_failed"), Severity.ERROR
            )
            self.main_page.update()
            return

        if response.status_code == 403:
            await self._expire_session()
            return

        self._collections = response.json().get("data") or []
        self._render()

    def _render(self) -> None:
        """Paint the cards, the count and the empty state.

        Every name listed here is kept, so the deeper screens do not have to ask for
        it again when they open (and do not paint an empty breadcrumb first).
        """
        self._lang = get_language()
        for row in self._collections:
            CollectionNames.remember(row.get("id"), row.get("name") or "")
        self._count.value = self.count_label(len(self._collections))
        self._grid.controls = [self._card(row) for row in self._collections]
        self._grid.visible = bool(self._collections)
        self._empty.visible = not self._collections
        self.main_page.update()

    def _card(self, collection: dict) -> CollectionCard:
        """A card of the grid, with the actions the page knows how to do."""
        card = CollectionCard(
            collection,
            self._lang,
            on_open=self._open_collection,
            on_rename=self._handle_rename,
            on_delete=self._handle_delete,
        )
        card.col = self.GRID_COLUMNS
        return card

    @staticmethod
    def count_label(count: int) -> str:
        """The counter next to the title, from the locale key."""
        return _("collections.count", count=count)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _handle_new(self, event: ft.ControlEvent) -> None:
        """Open the create dialog."""
        if self._service is None:
            return
        CollectionForm(
            self.main_page,
            self._service,
            on_saved=self._reload,
            on_forbidden=self._session_expired,
        ).show()

    def _handle_rename(self, collection: dict) -> None:
        """Open the rename dialog for one collection."""
        if self._service is None:
            return
        CollectionForm(
            self.main_page,
            self._service,
            collection=collection,
            on_saved=self._reload,
            on_forbidden=self._session_expired,
        ).show()

    def _handle_delete(self, collection: dict) -> None:
        """Ask before deleting one collection."""
        if self._service is None:
            return
        # Its name is remembered for the header; a deleted one is not asked again.
        CollectionNames.forget(collection.get("id") or 0)
        CollectionDeleteDialog(
            self.main_page,
            self._service,
            collection,
            on_deleted=self._reload,
            on_forbidden=self._session_expired,
        ).show()

    def _open_collection(self, collection_id: int) -> None:
        """Open the series of one collection."""
        self.main_page.run_task(self._push_collection, collection_id)

    async def _push_collection(self, collection_id: int) -> None:
        """Navigate to the collection's series."""
        await self.main_page.push_route(
            f"{URLs.Frontend.collections}/{collection_id}"
        )

    def _reload(self) -> None:
        """Ask again, after a write."""
        self.main_page.run_task(self.load_collections)

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
