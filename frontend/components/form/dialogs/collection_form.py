"""Dialogs for creating, renaming and deleting a collection (plan step A5).

Two builders, both `ft.AlertDialog` on `page.overlay` like the stamp form:

- `CollectionForm` creates a collection or renames one; the field is the name, and
  the same dialog serves both because the only thing that changes is the title and
  which call is made.
- `CollectionDeleteDialog` asks once, says what goes with the collection, and calls
  nobody until the user confirms.

A 403 is a session that expired: both close and tell the page, which sends the user
to the login. The dialogs never decide that on their own.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.colors import GREY_700, RED
from components.constants import CARD_BORDER_RADIUS, FONT_SIZE_XS
from components.form.text_field import TextField
from components.table.column_def import fmt_number
from core.base_ui import BaseUI
from core.translations import _, get_language
from services.collection_service import CollectionService


#: The client's signal that the JWT is no longer valid.
FORBIDDEN = 403

#: The server's answer when a collection was created or renamed.
SUCCESS = (200, 201)


class CollectionForm(BaseUI):
    """Create a collection, or rename an existing one.

    Args:
        page: the Flet page, where the dialog is opened.
        service: the collections service, already carrying the token.
        collection: the row to rename, or None to create a new one.
        on_saved: called after the API accepted the change.
        on_forbidden: called when the token is no longer valid.
    """

    WIDTH: int = 420

    def __init__(
        self,
        page: ft.Page,
        service: CollectionService,
        collection: Optional[dict] = None,
        on_saved: Optional[Callable[[], None]] = None,
        on_forbidden: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page = page
        self._service = service
        self._collection = collection
        self._on_saved = on_saved
        self._on_forbidden = on_forbidden

        # `expand=False` on purpose: a text field expands by default, and inside
        # the dialog's column that would stretch the dialog to the full height of
        # the window. The width comes from the dialog, not from the layout.
        self._name: TextField = TextField(
            label=_("collections.name_label"),
            max_length=100,
            autofocus=True,
            expand=False,
            width=self.WIDTH,
        )
        if collection is not None:
            self._name.value = collection.get("name") or ""
        self._error: ft.Text = ft.Text("", color=RED, size=FONT_SIZE_XS, visible=False)
        self._dialog: Optional[ft.AlertDialog] = None

    @property
    def is_rename(self) -> bool:
        """True when the dialog renames instead of creating."""
        return self._collection is not None

    def show(self) -> None:
        """Open the dialog."""
        title = (
            _("collections.rename_title")
            if self.is_rename
            else _("collections.new_title")
        )
        action = _("collections.rename") if self.is_rename else _("collections.create")

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=20, font_family="Roboto-Bold"),
            content=ft.Column(
                controls=[self._name, self._error],
                width=self.WIDTH,
                spacing=12,
                tight=True,
            ),
            actions=[
                DefaultButton(
                    text=_("collections.cancel"), on_click=self._close, expand=False
                ),
                PrimaryButton(text=action, on_click=self._submit, expand=False),
            ],
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dialog)
        self._dialog.open = True
        self.page.update()

    async def _submit(self, event: ft.ControlEvent) -> None:
        """Create or rename, and close on success."""
        name = (self._name.value or "").strip()
        if not name:
            self._show_error(_("collections.name_required"))
            return

        if self.is_rename:
            response = await self._service.update_collection(
                int(self._collection["id"]), name
            )
        else:
            response = await self._service.create_collection(name)

        if response is not None and response.status_code in SUCCESS:
            self._close()
            if self._on_saved is not None:
                self._on_saved()
            return

        if response is not None and response.status_code == FORBIDDEN:
            self._close()
            if self._on_forbidden is not None:
                self._on_forbidden()
            return

        self._show_error(_("collections.save_failed"))

    def _show_error(self, message: str) -> None:
        """Say what went wrong without closing the dialog."""
        self._error.value = message
        self._error.visible = True
        self.page.update()

    def _close(self, event: Optional[ft.ControlEvent] = None) -> None:
        """Close the dialog."""
        if self._dialog is not None:
            self._dialog.open = False
        self.page.update()


class CollectionDeleteDialog(BaseUI):
    """Delete a collection after one confirmation.

    Args:
        page: the Flet page, where the dialog is opened.
        service: the collections service, already carrying the token.
        collection: the row to delete.
        on_deleted: called after the API deleted it.
        on_forbidden: called when the token is no longer valid.
    """

    WIDTH: int = 420

    def __init__(
        self,
        page: ft.Page,
        service: CollectionService,
        collection: dict,
        on_deleted: Optional[Callable[[], None]] = None,
        on_forbidden: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page = page
        self._service = service
        self._collection = collection
        self._on_deleted = on_deleted
        self._on_forbidden = on_forbidden

        self._error: ft.Text = ft.Text("", color=RED, size=FONT_SIZE_XS, visible=False)
        self._dialog: Optional[ft.AlertDialog] = None

    def show(self) -> None:
        """Open the confirmation."""
        summary = _(
            "collections.summary",
            series=fmt_number(
                int(self._collection.get("series") or 0), get_language(), zero="0"
            ),
            stamps=fmt_number(
                int(self._collection.get("stamps") or 0), get_language(), zero="0"
            ),
        )

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                _("collections.delete_title"), size=20, font_family="Roboto-Bold"
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        _(
                            "collections.delete_message",
                            name=self._collection.get("name") or "",
                        )
                    ),
                    ft.Text(summary, size=FONT_SIZE_XS, color=GREY_700),
                    self._error,
                ],
                width=self.WIDTH,
                spacing=12,
                tight=True,
            ),
            actions=[
                DefaultButton(
                    text=_("collections.cancel"), on_click=self._close, expand=False
                ),
                AlertButton(
                    text=_("collections.delete_confirm"),
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
        """Delete the collection, and close when the API answers."""
        response = await self._service.delete_collection(
            int(self._collection["id"])
        )

        if response is not None and response.status_code == 200:
            self._close()
            if self._on_deleted is not None:
                self._on_deleted()
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
        """Close the dialog without deleting."""
        if self._dialog is not None:
            self._dialog.open = False
        self.page.update()
