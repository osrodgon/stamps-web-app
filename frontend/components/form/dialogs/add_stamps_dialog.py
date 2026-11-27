"""Adding stamps to a collection from the catalogue (plan step C4).

The dialog that opens the door of a collection: it searches the catalogue, shows one
row per series with how much of it the collection already holds, unfolds a series to
add one stamp, and adds a whole year from the footer when a single year is filtered.
Every write goes through the bulk endpoint of C1 — one request per action, never a
loop of adds — and the dialog stays open afterwards, saying what happened, so a
collection can be filled without opening it again.

It follows the mockup `memory-bank/mockups/add-stamps-dialog.html`: the house
`TextField` for the filters, the chevron to unfold a row, and
`PrimaryButton`/`DefaultButton` for the actions.
"""

from __future__ import annotations

import asyncio
import os
from typing import Callable, Optional

import flet as ft

from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.colors import BG_ALT, GREY_700, RED, ROW_BORDER
from components.constants import (
    CARD_BORDER_RADIUS,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    FONT_SIZE_XS,
)
from components.form.text_field import TextField
from components.table.column_def import fmt_date, fmt_number
from core.base_ui import BaseUI
from core.translations import _, get_language
from services.catalogue_service import CatalogueService
from settings import ASSETS_DIR, IMAGE_DIR, NO_STAMP

#: The status codes that mean the write happened.
SUCCESS = (200, 201)
FORBIDDEN = 403
#: The cap of the endpoint; over it the answer is a 400 and nothing is written.
TOO_MANY = 400
#: How long the dialog waits after a keystroke before asking the catalogue.
DEBOUNCE_DELAY = 0.3
#: Series per request. A year can hold more than a dialog should list at once.
PAGE_SIZE = 20
#: From this many stamps on, the dialog asks first.
CONFIRM_ABOVE = 20


class AddStampsDialog(BaseUI):
    """Search the catalogue and add stamps, a series or a whole year.

    Args:
        page: the Flet page, where the dialog is opened.
        service: the catalogue service, already carrying the token.
        collection_id: the collection the copies go into.
        collection_name: its name, for the title.
        on_added: called with `(created, skipped)` after each write, so the screen
            behind can reload.
        on_forbidden: called when the token is no longer valid.
    """

    WIDTH: int = 900

    def __init__(
        self,
        page: ft.Page,
        service: CatalogueService,
        collection_id: int,
        collection_name: str = "",
        on_added: Optional[Callable[[int, int], None]] = None,
        on_forbidden: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page = page
        self._service = service
        self._collection_id = collection_id
        self._collection_name = collection_name
        self._on_added = on_added
        self._on_forbidden = on_forbidden
        self._lang: str = get_language()

        self._dialog: Optional[ft.AlertDialog] = None
        self._confirm: Optional[ft.AlertDialog] = None

        #: What the search found, in the order it came.
        self._issues: list[dict] = []
        self._page: int = 1
        self._has_more: bool = False
        #: Stamps of the year the footer offers, or None when no single year is set.
        self._year: Optional[int] = None
        self._year_stamps: Optional[int] = None

        self._name_task: Optional[asyncio.Task] = None
        self._year_task: Optional[asyncio.Task] = None
        self._detail_tasks: dict[int, asyncio.Task] = {}

        self._name_field: TextField = TextField(
            label=_("collections.filter_series"),
            hint_text=_("collections.filter_name"),
            on_change=self._on_name_change,
            expand=True,
        )
        self._from_field: TextField = self._year_field(
            "collections.filter_from_year"
        )
        self._to_field: TextField = self._year_field("collections.filter_to_year")

        self._status: ft.Text = ft.Text(
            "", size=FONT_SIZE_XS, color=GREY_700, visible=False
        )
        self._error: ft.Text = ft.Text(
            "", size=FONT_SIZE_XS, color=RED, visible=False
        )
        self._results: ft.ListView = ft.ListView(
            controls=[],
            spacing=8,
            padding=ft.Padding.only(right=10),
            expand=True,
        )
        #: The list is bounded so a page of twenty does not push the actions away,
        #: and padded so the floating scrollbar does not paint over the rows.
        self._results_box: ft.Container = ft.Container(
            height=360, content=self._results
        )
        self._empty: ft.Text = ft.Text(
            _("collections.empty_series"), size=FONT_SIZE_DEFAULT, color=GREY_700
        )
        self._empty.visible = False
        self._load_more: DefaultButton = DefaultButton(
            text=_("collections.load_more"),
            on_click=self._load_next,
            expand=False,
        )
        self._load_more.visible = False
        self._year_button: PrimaryButton = PrimaryButton(
            text=_("collections.add_every_stamp", year=0, count=0),
            on_click=self._add_year,
            expand=False,
        )
        self._year_button.visible = False
        self._year_hint: ft.Text = ft.Text("", size=FONT_SIZE_XS, color=GREY_700)
        self._footer_hint: ft.Text = ft.Text(
            _("collections.add_stamps_hint"),
            size=FONT_SIZE_XS,
            color=GREY_700,
        )

    # ------------------------------------------------------------------
    # Opening
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Open the dialog and run the first search."""
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                _("collections.add_stamps_title"),
                size=20,
                font_family="Roboto-Bold",
            ),
            bgcolor=ft.Colors.WHITE,
            content=ft.Container(
                width=self.WIDTH,
                content=ft.Column(
                    controls=[
                        self.__subtitle(),
                        self.__filters(),
                        self._error,
                        self._results_box,
                        self._empty,
                        self._load_more,
                        self.__footer(),
                    ],
                    spacing=12,
                    tight=True,
                ),
            ),
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dialog)
        self._dialog.open = True
        self.page.update()
        self.page.run_task(self._search)

    def __footer(self) -> ft.Row:
        """The hint or the counts on the left, the actions on the right.

        It lives inside the content and not in `actions`: that one is a wrapping Row,
        and an expanding spacer there stacks the buttons (the B5 trap again).
        """
        return ft.Row(
            controls=[
                self._footer_hint,
                self._year_hint,
                self._status,
                ft.Container(expand=True),
                DefaultButton(
                    text=_("collections.cancel"),
                    on_click=self._close,
                    expand=False,
                ),
                self._year_button,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def __subtitle(self) -> ft.Text:
        """`The catalogue, into Test.` — where the copies go."""
        name = (self._collection_name or "").strip()
        text = (
            _("collections.add_stamps_into", name=name)
            if name
            else _("collections.add_stamps_hint")
        )
        return ft.Text(text, size=FONT_SIZE_XS, color=GREY_700)

    def __filters(self) -> ft.Row:
        """The two filters of the screen behind, in the same order."""
        return ft.Row(
            controls=[self._name_field, self._from_field, self._to_field],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------

    async def _on_name_change(self, event: ft.ControlEvent) -> None:
        """Debounce the name filter."""
        if self._name_task is not None:
            self._name_task.cancel()
        self._name_task = asyncio.create_task(self._search_after_debounce())

    async def _on_year_change(self, event: ft.ControlEvent) -> None:
        """Debounce the two year boxes."""
        if self._year_task is not None:
            self._year_task.cancel()
        self._year_task = asyncio.create_task(self._search_after_debounce())

    async def _search_after_debounce(self) -> None:
        """Ask the catalogue once the typing stops."""
        await asyncio.sleep(DEBOUNCE_DELAY)
        await self._search()

    async def _search(self) -> None:
        """Read the first page of what the filters name."""
        self._page = 1
        self._error.visible = False
        await self.load()

    async def load(self) -> None:
        """Fetch the current page and paint it."""
        self._year = self.year_of(self._from_field.value, self._to_field.value)

        response = await self._service.search_issues(
            self._collection_id,
            page=self._page,
            page_size=PAGE_SIZE,
            name=(self._name_field.value or "").strip(),
            year=self.year_filter(self._from_field.value, self._to_field.value),
            sort_by="date",
            order="asc",
        )

        if response is None or response.status_code not in (200, FORBIDDEN):
            self.__show_error(_("collections.load_failed"))
            return
        if response.status_code == FORBIDDEN:
            self._forbidden()
            return

        data = response.json().get("data") or {}
        issues = data.get("issues") or []
        pagination = data.get("pagination") or {}
        self._has_more = bool(pagination.get("has_more"))
        self._issues = issues if self._page == 1 else self._issues + issues

        await self.__count_year()
        self._render()
        self.__update_year_action()

    async def __count_year(self) -> None:
        """How many stamps the year the boxes name has, if they name one.

        The page in hand is filtered (and a page of twenty), so it cannot answer
        that: the year is asked on its own, with `pageSize=0` and no name filter,
        and its `total_stamps` are added up. One request, only when a year is set.
        """
        if self._year is None:
            self._year_stamps = None
            return

        year = self._year
        response = await self._service.search_issues(
            self._collection_id,
            page=1,
            page_size=0,
            name="",
            year=f"{year}-{year}",
            sort_by="date",
            order="asc",
        )
        if response is None or response.status_code != 200:
            self._year_stamps = None
            return

        rows = (response.json().get("data") or {}).get("issues") or []
        self._year_stamps = sum(
            int(issue.get("total_stamps") or 0) for issue in rows
        )

    def _render(self) -> None:
        """Paint the rows and the empty state."""
        self._results.controls = [self.__row(issue) for issue in self._issues]
        self._empty.visible = not self._issues
        self._load_more.visible = self._has_more
        self.page.update()

    @staticmethod
    def year_filter(from_value: Optional[str], to_value: Optional[str]) -> str:
        """The `year` parameter from the two boxes, as the screen behind builds it."""
        start = AddStampsDialog.__year(from_value)
        end = AddStampsDialog.__year(to_value)

        if start is not None and end is not None:
            return f"{start}-{end}"
        if start is not None:
            return f"{start}-"
        if end is not None:
            return f"-{end}"
        return ""

    @staticmethod
    def year_of(from_value: Optional[str], to_value: Optional[str]) -> Optional[int]:
        """The one year the boxes name, or None when they name none or two.

        One box is enough: `From 1852` lists everything from 1852 on, and the
        footer's action still says which year it adds, so typing the same year
        twice just to reach it is not required.
        """
        start = AddStampsDialog.__year(from_value)
        end = AddStampsDialog.__year(to_value)
        if start is not None and end is not None and start != end:
            return None
        return start if start is not None else end

    @staticmethod
    def __year(value: Optional[str]) -> Optional[int]:
        """One box as a year, or None when it is empty or not a number."""
        text = (value or "").strip()
        if not text.isdigit():
            return None
        return int(text)

    async def _load_next(self, event: ft.ControlEvent) -> None:
        """Append the next page of the search."""
        if not self._has_more:
            return
        self._page += 1
        await self.load()

    # ------------------------------------------------------------------
    # One row of the catalogue
    # ------------------------------------------------------------------

    def __row(self, issue: dict) -> ft.Control:
        """One series: cover, identity, what is held and what can be done."""
        total = int(issue.get("total_stamps") or 0)
        owned = int(issue.get("owned_stamps") or 0)
        missing = max(0, total - owned)
        expanded = issue.get("id") in self._expanded_ids()

        controls: list[ft.Control] = [
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ROW_BORDER),
                border_radius=CARD_BORDER_RADIUS,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                content=ft.Row(
                    controls=[
                        self.__cover(issue),
                        self.__identity(issue),
                        self.__held(owned, total),
                        ft.IconButton(
                            icon=(
                                ft.Icons.KEYBOARD_ARROW_UP
                                if expanded
                                else ft.Icons.KEYBOARD_ARROW_DOWN
                            ),
                            tooltip=_(
                                "collections.hide_stamps"
                                if expanded
                                else "collections.show_stamps"
                            ),
                            on_click=lambda event, row=issue: self.page.run_task(
                                self._toggle, row
                            ),
                        ),
                        self.__add_series_button(issue, missing),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        ]
        if expanded:
            controls.append(self.__stamps(issue))
        return ft.Column(controls=controls, spacing=6, tight=True)

    def _expanded_ids(self) -> set[int]:
        """The series whose stamp list is open."""
        return {
            int(issue.get("id") or 0)
            for issue in self._issues
            if issue.get("detail") is not None
        }

    def __cover(self, issue: dict) -> ft.Container:
        """The series' picture, or the plate."""
        cover = issue.get("cover") or {}
        source = self.__picture(cover.get("year"), cover.get("code"))
        return ft.Container(
            width=48,
            height=44,
            bgcolor=BG_ALT,
            border=ft.Border.all(1, ROW_BORDER),
            border_radius=4,
            alignment=ft.Alignment.CENTER,
            content=ft.Image(
                src=source, width=42, height=38, fit=ft.BoxFit.CONTAIN
            ),
        )

    @staticmethod
    def __picture(year, code) -> str:
        """The picture of a cover, or the placeholder."""
        if year is not None and code:
            path = os.path.join(IMAGE_DIR, str(year), f"{code}.webp")
            if os.path.exists(path):
                return os.path.join(
                    os.path.relpath(IMAGE_DIR, ASSETS_DIR),
                    str(year),
                    f"{code}.webp",
                )
        return NO_STAMP

    def __identity(self, issue: dict) -> ft.Column:
        """The date, the name and what kind of series it is."""
        where = " · ".join(
            part
            for part in (issue.get("country"), issue.get("stamp_type"))
            if part
        )
        return ft.Column(
            controls=[
                ft.Text(
                    f"{issue.get('year') or ''} · "
                    f"{fmt_date(issue.get('date') or '', self._lang)}",
                    size=FONT_SIZE_XS,
                    color=GREY_700,
                ),
                ft.Text(
                    issue.get("name") or "",
                    size=FONT_SIZE_SMALL_HEADING,
                    weight=ft.FontWeight.BOLD,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    where,
                    size=FONT_SIZE_XS,
                    color=GREY_700,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=0,
            tight=True,
            expand=True,
        )

    @staticmethod
    def __held(owned: int, total: int) -> ft.Text:
        """`2 of 5 in this collection`."""
        lang = get_language()
        return ft.Text(
            _(
                "collections.held_of",
                owned=fmt_number(owned, lang, zero="0"),
                total=fmt_number(total, lang, zero="0"),
            ),
            size=FONT_SIZE_XS,
            color=GREY_700,
        )

    def __add_series_button(self, issue: dict, missing: int) -> ft.Control:
        """`Add the series`, `Add the missing 2` or `Already complete`."""
        if missing == 0:
            button = DefaultButton(
                text=_("collections.already_complete"), expand=False
            )
            button.disabled = True
            return button

        text = (
            _("collections.add_the_series")
            if missing == int(issue.get("total_stamps") or 0)
            else _("collections.add_the_missing", count=missing)
        )
        return DefaultButton(
            text=text,
            on_click=lambda event, row=issue, count=missing: self.page.run_task(
                self._add_issue, row, count
            ),
            expand=False,
        )

    def __stamps(self, issue: dict) -> ft.Control:
        """The stamps of an unfolded series, one card each."""
        detail = issue.get("detail") or {}
        stamps = detail.get("stamps") or []
        return ft.GridView(
            controls=[self.__stamp(stamp) for stamp in stamps],
            runs_count=5,
            spacing=10,
            run_spacing=10,
            height=self.__stamps_height(len(stamps)),
        )

    @staticmethod
    def __stamps_height(count: int) -> int:
        """The height of the unfolded grid, so the dialog does not jump."""
        rows = max(1, (count + 4) // 5)
        return rows * 150

    def __stamp(self, stamp: dict) -> ft.Control:
        """One stamp: plate, name, face value and colour, and its action."""
        owned = stamp.get("item") is not None
        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ROW_BORDER),
            border_radius=CARD_BORDER_RADIUS,
            padding=8,
            content=ft.Column(
                controls=[
                    ft.Container(
                        height=64,
                        bgcolor=BG_ALT,
                        border_radius=4,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Image(
                            src=self.__picture(
                                stamp.get("issue_year"), stamp.get("fesofi_code")
                            ),
                            height=60,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                    ),
                    ft.Text(
                        stamp.get("name") or "",
                        size=FONT_SIZE_XS,
                        weight=ft.FontWeight.W_600,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        " · ".join(
                            part
                            for part in (
                                stamp.get("face_value"),
                                ", ".join(stamp.get("colors") or []),
                            )
                            if part
                        ),
                        size=FONT_SIZE_XS,
                        color=GREY_700,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    (
                        ft.Text(
                            _("collections.in_this_collection"),
                            size=FONT_SIZE_XS,
                            color=ft.Colors.GREEN_700,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        )
                        if owned
                        else DefaultButton(
                            text=_("collections.add_one"),
                            on_click=lambda event, row=stamp: self.page.run_task(
                                self._add_stamp, row
                            ),
                            expand=False,
                        )
                    ),
                ],
                spacing=6,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    async def _toggle(self, issue: dict) -> None:
        """Open or close the stamps of one series, reading them the first time."""
        if issue.get("detail") is not None:
            issue["detail"] = None
            self._render()
            return

        response = await self._service.get_issue(
            self._collection_id, int(issue.get("id") or 0)
        )
        if response is None or response.status_code not in (200, FORBIDDEN):
            self.__show_error(_("collections.load_failed"))
            return
        if response.status_code == FORBIDDEN:
            self._forbidden()
            return

        detail = response.json().get("data") or {}
        # The stamp payload carries no year, and the picture is `<year>/<code>`:
        # the detail's issue is where it comes from, as the series screen does.
        year = (detail.get("issue") or {}).get("year")
        for stamp in detail.get("stamps") or []:
            stamp["issue_year"] = year
        issue["detail"] = detail
        self._render()

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    async def _add_issue(self, issue: dict, count: int) -> None:
        """Add the stamps of one series that the collection is missing."""
        if count > CONFIRM_ABOVE:
            self._ask(count, lambda: self.__write_issue(issue))
            return
        await self.__write_issue(issue)

    async def _add_stamp(self, stamp: dict) -> None:
        """Add one stamp."""
        await self.__write(lambda: self._service.add_stamps(
            self._collection_id, [int(stamp.get("id") or 0)]
        ))

    async def _add_year(self, event: ft.ControlEvent) -> None:
        """Add every stamp of the year both boxes hold."""
        if self._year is None:
            return
        count = self._year_stamps or 0
        if count > CONFIRM_ABOVE:
            self._ask(count, self.__write_year)
            return
        await self.__write_year()

    async def __write_issue(self, issue: dict) -> None:
        """Add a series through the bulk endpoint."""
        await self.__write(
            lambda: self._service.add_issue(
                self._collection_id, int(issue.get("id") or 0)
            )
        )

    async def __write_year(self) -> None:
        """Add a year through the bulk endpoint."""
        if self._year is None:
            return
        year = self._year
        await self.__write(
            lambda: self._service.add_year(self._collection_id, year)
        )

    async def __write(self, call: Callable) -> None:
        """Run one write, paint what it answered and report it."""
        response = await call()

        if response is None:
            self.__show_error(_("collections.save_failed"))
            return
        if response.status_code == FORBIDDEN:
            self._forbidden()
            return
        if response.status_code not in SUCCESS:
            self.__show_error(self.__refusal(response))
            return

        data = response.json().get("data") or {}
        created = int(data.get("created") or 0)
        skipped = int(data.get("skipped") or 0)
        self._status.value = (
            f"{_('collections.added_count', count=created)} · "
            f"{_('collections.skipped_count', count=skipped)}"
        )
        self._status.visible = True
        self._error.visible = False
        if self._on_added is not None:
            self._on_added(created, skipped)
        await self.load()

    @staticmethod
    def __refusal(response) -> str:
        """The first message the API sent, or a generic one."""
        try:
            errors = response.json().get("errors") or []
            if errors and isinstance(errors, list):
                message = errors[0].get("message")
                if message:
                    return str(message)
        except (ValueError, AttributeError, TypeError):
            pass
        return _("collections.save_failed")

    def _ask(self, count: int, accepted: Callable) -> None:
        """Ask before a big add, and only then write."""
        self._confirm = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            title=ft.Text(
                _("collections.add_confirmation", count=count),
                size=18,
                font_family="Roboto-Bold",
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        _(
                            "collections.add_confirmation_into",
                            name=self._collection_name,
                        ),
                        size=FONT_SIZE_DEFAULT,
                    ),
                    ft.Text(
                        _("collections.add_confirmation_note"),
                        size=FONT_SIZE_XS,
                        color=GREY_700,
                    ),
                ],
                spacing=8,
                tight=True,
                width=380,
            ),
            actions=[
                DefaultButton(
                    text=_("collections.cancel"),
                    on_click=self._close_confirm,
                    expand=False,
                ),
                PrimaryButton(
                    text=_("collections.add_one"),
                    on_click=lambda event: self.page.run_task(
                        self._confirm_and_write, accepted
                    ),
                    expand=False,
                ),
            ],
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._confirm)
        self._confirm.open = True
        self.page.update()

    async def _confirm_and_write(self, accepted: Callable) -> None:
        """Close the question and run the write it accepted."""
        self._close_confirm()
        await accepted()

    def _close_confirm(self, event: Optional[ft.ControlEvent] = None) -> None:
        """Close the confirmation without writing."""
        if self._confirm is not None:
            self._confirm.open = False
        self.page.update()

    # ------------------------------------------------------------------
    # Footer, errors and closing
    # ------------------------------------------------------------------

    def __update_year_action(self) -> None:
        """Offer the year action only when both boxes hold the same year."""
        if self._year is None:
            self._year_button.visible = False
            self._year_hint.value = ""
            self._footer_hint.visible = True
        else:
            count = self._year_stamps or 0
            self._year_button.content.value = _(
                "collections.add_every_stamp",
                year=self._year,
                count=fmt_number(count, self._lang, zero="0"),
            )
            self._year_button.visible = True
            self._year_hint.value = _(
                "collections.stamps_found",
                series=fmt_number(len(self._issues), self._lang, zero="0"),
                stamps=fmt_number(count, self._lang, zero="0"),
            )
            self._footer_hint.visible = False
        self.page.update()

    def __show_error(self, message: str) -> None:
        """Say what went wrong without closing the dialog."""
        self._error.value = message
        self._error.visible = True
        self.page.update()

    def _forbidden(self) -> None:
        """Close and let the page take the user to the login."""
        self._close()
        if self._on_forbidden is not None:
            self._on_forbidden()

    def _close(self, event: Optional[ft.ControlEvent] = None) -> None:
        """Close the dialog."""
        if self._dialog is not None:
            self._dialog.open = False
        self.page.update()
