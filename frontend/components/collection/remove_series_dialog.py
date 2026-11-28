"""Taking a series out of a collection, after one question (plan D3).

It is the dialog the detail already had, moved out so the series list can use it
too: the two screens ask the same thing, call the same endpoint and reload in their
own way, which is why the dialog reports what happened instead of deciding what to
do next.

The copies leave the collection; the catalogue keeps the series and its stamps.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.colors import GREY_700, RED
from components.constants import CARD_BORDER_RADIUS, FONT_SIZE_XS
from core.base_ui import BaseUI
from core.translations import _
from services.collection_item_service import CollectionItemService

FORBIDDEN = 403
SUCCESS = (200, 204)


class RemoveSeriesDialog(BaseUI):
    """Ask once and delete the caller's copies of one series.

    Args:
        page: the Flet page, where the dialog is opened.
        service: the item service, already carrying the token.
        collection_id: the collection the copies leave.
        issue_id: the series whose copies are removed.
        name: the series' name, for the question.
        count: how many copies leave, for the question.
        on_removed: called with how many copies went, after the API deleted them.
        on_forbidden: called when the token is no longer valid.
    """

    WIDTH: int = 420

    def __init__(
        self,
        page: ft.Page,
        service: CollectionItemService,
        collection_id: int,
        issue_id: int,
        name: str,
        count: int,
        on_removed: Optional[Callable[[int], None]] = None,
        on_forbidden: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page = page
        self._service = service
        self._collection_id = collection_id
        self._issue_id = issue_id
        self._name = name
        self._count = count
        self._on_removed = on_removed
        self._on_forbidden = on_forbidden

        self._error: ft.Text = ft.Text(
            "", color=RED, size=FONT_SIZE_XS, visible=False
        )
        self._dialog: Optional[ft.AlertDialog] = None

    def show(self) -> None:
        """Open the confirmation."""
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                _("collections.remove_series"),
                size=20,
                font_family="Roboto-Bold",
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        _(
                            "collections.remove_series_message",
                            name=self._name,
                            count=self._count,
                        )
                    ),
                    self._error,
                ],
                width=self.WIDTH,
                spacing=12,
                tight=True,
            ),
            actions=[
                DefaultButton(
                    text=_("collections.cancel"),
                    on_click=self._close,
                    expand=False,
                ),
                AlertButton(
                    text=_("collections.remove"),
                    on_click=self._confirm,
                    expand=False,
                ),
            ],
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dialog)
        self._dialog.open = True
        self.page.update()

    async def _confirm(self, event: ft.ControlEvent) -> None:
        """Delete the copies, and close when the API answers."""
        response = await self._service.remove_issue(
            self._collection_id, self._issue_id
        )

        if response is not None and response.status_code in SUCCESS:
            deleted = int((response.json().get("data") or {}).get("deleted") or 0)
            self._close()
            if self._on_removed is not None:
                self._on_removed(deleted)
            return

        if response is not None and response.status_code == FORBIDDEN:
            self._close()
            if self._on_forbidden is not None:
                self._on_forbidden()
            return

        self._error.value = _("collections.delete_failed")
        self._error.visible = True
        self.page.update()

    def _close(self, event: Optional[ft.ControlEvent] = None) -> None:
        """Close the dialog."""
        if self._dialog is not None:
            self._dialog.open = False
        self.page.update()
