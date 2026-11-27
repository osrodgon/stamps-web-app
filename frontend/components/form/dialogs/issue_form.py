import datetime
from typing import Any, Callable, Optional

import flet as ft
import requests

from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_PADDING,
    DIALOG_WIDTH,
)
from components.table.issue_detail.issue_header_section import IssueHeaderSection
from components.table.issue_detail.issue_specs_grid import IssueSpecsGrid
from core.base_ui import BaseUI
from core.severity import Severity
from core.logger import Logger
from core.translations import _, get_language
from core.utils import get_local_today
from services.issue_service import IssueService


class IssueForm(BaseUI, Logger):
    """AlertDialog-based form for creating a new stamp issue.

    Uses the same ``IssueHeaderSection`` and ``IssueSpecsGrid`` components
    as ``IssueDetailCard`` edit mode, wrapped in a dialog with Cancel /
    Create buttons at the bottom.

    Attributes:
        page: The Flet page instance.
        _service: The IssueService for API calls.
        _on_success: Callback fired after successful creation (sync only).
    """

    def __init__(
        self,
        page: ft.Page,
        issue_service: IssueService,
        on_success: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.page: ft.Page = page
        self._service: IssueService = issue_service
        self._on_success: Optional[Callable[[], None]] = on_success

        self._dlg: Optional[ft.AlertDialog] = None
        self._header_section: Optional[IssueHeaderSection] = None
        self._specs_grid: Optional[IssueSpecsGrid] = None
        self._years: list[dict] = []

    # --- Lifecycle ---

    async def show(self) -> None:
        """Fetch reference data and display the form dialog."""
        empty_issue: dict = {
            "id": None,
            "name": "",
            "market_value_mnh": None,
            "market_value_used": None,
            "total_printed": None,
            "country": None,
            "stamp_type": None,
            "printer": None,
            "print_type": None,
            "artist": None,
            "paper_type": None,
            "perforation": None,
            "year": None,
            "description": "",
            "note": "",
            "date": get_local_today().isoformat(),
        }

        self._header_section = IssueHeaderSection(
            issue=empty_issue,
            lang=get_language(),
            hide_action_icons=True,
        )
        self._specs_grid = IssueSpecsGrid(issue=empty_issue)

        self._dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("issues.add_title"), font_family="Roboto-Bold"),
            content=ft.Column(
                controls=[
                    ft.Container(height=200),
                    ft.Row(
                        controls=[ft.ProgressRing()],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[ft.Text(_("ui.loading"))],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                width=DIALOG_WIDTH,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dlg)
        self._dlg.open = True
        self.page.update()

        # Fetch years (specs grid fetches the other ref data internally)
        years_response = await self._service.get_years()
        if years_response and years_response.status_code == requests.codes.ok:
            try:
                self._years = years_response.json().get("data", [])
            except Exception:
                self._years = []
        else:
            self._years = []

        # Enter permanent edit mode on both shared components
        specs_ok: bool = await self._specs_grid.enter_edit_mode(self._service)
        if not specs_ok:
            self.close()
            await self.show_notification(
                _("issues.creation_failed"), severity=Severity.ERROR
            )
            return

        self._header_section.enter_edit_mode(
            _("issues.hint_name"), page=self.page
        )

        self._rebuild_content()
        self.page.update()

    def _rebuild_content(self) -> None:
        """Replace the loading spinner with the full form layout."""
        cancel_btn = DefaultButton(
            text=_("ui.cancel").upper(),
            on_click=self._on_cancel,
            expand=False,
        )
        create_btn = PrimaryButton(
            text=_("issues.create").upper(),
            on_click=self._on_create,
            expand=False,
        )

        content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._header_section,
                            self._specs_grid,
                        ],
                        spacing=12,
                    ),
                    padding=CARD_PADDING,
                ),
                ft.Row(
                    controls=[cancel_btn, create_btn],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            width=DIALOG_WIDTH,
            spacing=0,
        )

        if self._dlg:
            self._dlg.content = content

    def close(self) -> None:
        """Close the dialog and clean up."""
        if self._dlg:
            self._dlg.open = False
            self.page.update()

    # --- Event handlers ---

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Close the form dialog without saving.

        Args:
            e: The click event from the Cancel button.
        """
        self.close()

    async def _on_create(self, e: ft.ControlEvent) -> None:
        """Validate and submit the form to create a new issue.

        Args:
            e: The click event from the Create Issue button.
        """
        self.log.debug("Validating required fields...")

        name_val: str = self._header_section.name_text.strip() if self._header_section and self._header_section.name_text else ""
        if not name_val:
            await self.show_notification(_("issues.name_required"), severity=Severity.ERROR)
            return

        mint_val: float = self._header_section.mint_value
        if mint_val < 0:
            await self.show_notification(_("issues.mint_value_invalid"), severity=Severity.ERROR)
            return

        used_val: float = self._header_section.used_value
        total_val: int = self._header_section.total_printed_value
        desc_val: str = self._specs_grid.description_value
        notes_val: str = self._specs_grid.notes_value
        date_val: str = self._header_section.date_value

        payload: dict[str, Any] = {
            "name": name_val,
            "market_value_mnh": str(mint_val),
            "market_value_used": str(used_val),
            "total_printed": str(total_val),
            "description": desc_val,
            "note": notes_val,
            "date": date_val,
            "perforation": self._specs_grid.perforation_value,
        }

        self.log.debug("Resolving reference data...")
        for key, state in self._specs_grid.edit_state.items():
            ac = state["ac"]
            sid: Optional[int] = ac.selected_id
            text: str = ac.text

            if sid is None and text:
                sid = await state["create"](self._service, text)
                if sid is None:
                    await self.show_notification(
                        _("issues.creation_failed"), severity=Severity.ERROR
                    )
                    return

            payload[state["issue_key"]] = sid

        # Resolve year from the selected date
        year_number: int = (
            datetime.date.fromisoformat(date_val).year
            if date_val else get_local_today().year
        )
        year_id: Optional[int] = None
        for year_obj in self._years:
            if year_obj.get("year") == year_number:
                year_id = year_obj.get("id")
                break

        if year_id is None:
            year_id = await self._service.create_year(year_number)
            if year_id is None:
                await self.show_notification(
                    _("issues.creation_failed"), severity=Severity.ERROR
                )
                return

        payload["year"] = year_id

        self.log.debug(f"About to call create_issue with payload: {payload}")
        try:
            response = await self._service.create_issue(payload)
            if response and response.status_code in (200, 201):
                self.close()
                if self._on_success:
                    self._on_success()
                await self.show_notification(
                    _("issues.creation_success"), severity=Severity.SUCCESS
                )
            else:
                error_msg = _("issues.creation_failed")
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_msg)
                    except Exception:
                        pass
                self.log.error(f"Failed to create issue: {error_msg}")
                await self.show_notification(error_msg, severity=Severity.ERROR)
        except Exception as exc:
            self.log.error(f"{exc}")
            await self.show_notification(
                _("issues.network_error"), severity=Severity.ERROR
            )
