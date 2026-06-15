"""Issue detail card component — expanded issue details with stamps grid."""

from typing import Any, Callable, Optional

import flet as ft

from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.form.auto_complete_field import AutoCompleteField
from components.table.column_def import COLUMNS
from components.table.issue_detail.issue_header_section import IssueHeaderSection
from components.table.issue_detail.issue_specs_grid import IssueSpecsGrid
from components.table.issue_detail.issue_stamp_grid import IssueStampGrid
from core.base_ui import BaseUI
from core.severity import Severity
from core.translations import _
from components.constants import CARD_BORDER_RADIUS, CARD_PADDING
from services.issue_service import IssueService


class IssueDetailCard(ft.Container, BaseUI):
    """Expanded detail card showing full issue information and stamps.

    Coordinates three child sections (header, specs grid, stamp grid)
    and manages the edit-mode lifecycle (enter, save, cancel).

    Args:
        issue: Raw issue data dict from the API response.
        stamps: List of stamp dicts wrapped in a dict with a "data" key.
        lang: Language code ("en" or "es").
        loading: If True, shows a loading placeholder in the stamp section.
        service: IssueService for fetching reference data and saving changes.
        on_edit_stamp: Called with (stamp_dict, issue_id) when the edit icon is clicked.
        on_delete_stamp: Called with (stamp_id, issue_id) when delete is clicked.
        on_edit_issue: Called with issue ID after a successful edit save.
        on_delete_issue: Called with issue ID when the issue delete icon is clicked.
        on_add_stamp: Called with issue ID when the add-stamp button is clicked.
    """

    def __init__(
        self,
        issue: dict,
        stamps: dict,
        lang: str,
        loading: bool = False,
        service: Optional[IssueService] = None,
        on_edit_stamp: Optional[Callable[[dict, int], Any]] = None,
        on_delete_stamp: Optional[Callable[[int, int], Any]] = None,
        on_edit_issue: Optional[Callable[[int], Any]] = None,
        on_delete_issue: Optional[Callable[[int], Any]] = None,
        on_add_stamp: Optional[Callable[[int], Any]] = None,
    ) -> None:
        super().__init__()
        self._issue: dict = issue
        self._service: Optional[IssueService] = service
        self._on_edit_issue: Optional[Callable[[int], Any]] = on_edit_issue
        self._on_delete_issue: Optional[Callable[[int], Any]] = on_delete_issue
        self._on_add_stamp: Optional[Callable[[int], Any]] = on_add_stamp
        self._editing: bool = False

        wrapped_on_delete_stamp = (
            (lambda sid: on_delete_stamp(sid, self._issue["id"]))
            if on_delete_stamp is not None else None
        )

        wrapped_on_edit_stamp = (
            (lambda stamp: on_edit_stamp(stamp, self._issue["id"]))
            if on_edit_stamp is not None else None
        )

        self._header_section = IssueHeaderSection(
            issue=issue,
            lang=lang,
            on_edit_click=self._handle_edit_issue,
            on_delete_click=self._handle_delete_issue,
            on_save_click=self._handle_save_edit,
            on_cancel_click=self._handle_cancel_edit,
        )
        self._specs_grid = IssueSpecsGrid(issue=issue)
        self._stamp_grid = IssueStampGrid(
            stamps=stamps,
            loading=loading,
            lang=lang,
            issue_year=str(issue.get("year", "")),
            on_edit_stamp=wrapped_on_edit_stamp,
            on_delete_stamp=wrapped_on_delete_stamp,
            on_add_stamp=self._handle_add_stamp,
        )

        self.padding = CARD_PADDING
        self.bgcolor = ft.Colors.BLUE_GREY_50
        self.content = ft.Column(
            controls=[
                self._header_section,
                self._specs_grid,
                self._stamp_grid,
            ],
            spacing=12,
        )

    def _safe_update(self) -> None:
        try:
            self.update()
        except RuntimeError:
            pass

    # --- Edit mode lifecycle ---

    async def _handle_edit_issue(self, e: ft.ControlEvent) -> None:
        if self._editing or not self._service:
            return
        self._editing = True
        ok: bool = await self._specs_grid.enter_edit_mode(self._service)
        if not ok:
            self._editing = False
            return
        self._header_section.enter_edit_mode(_("issues.hint_name"), page=self.page)
        self._safe_update()

    async def _handle_save_edit(self, e: ft.ControlEvent) -> None:
        name_value: str = self._header_section.name_text
        if not name_value:
            await self.show_notification(_("issues.name_required"), Severity.ERROR)
            return

        mint_val: float = self._header_section.mint_value
        if mint_val < 0:
            await self.show_notification(_("issues.mint_value_invalid"), Severity.ERROR)
            return

        used_val: float = self._header_section.used_value
        total_val: int = self._header_section.total_printed_value
        desc_val: str = self._specs_grid.description_value
        notes_val: str = self._specs_grid.notes_value
        date_val: str = self._header_section.date_value

        payload: dict[str, Any] = {
            "name": name_value,
            "market_value_mnh": str(mint_val),
            "market_value_used": str(used_val),
            "total_printed": str(total_val),
            "description": desc_val,
            "note": notes_val,
            "date": date_val,
        }

        for key, state in self._specs_grid.edit_state.items():
            ac: AutoCompleteField = state["ac"]
            sid: Optional[int] = ac.selected_id
            text: str = ac.text

            if sid is None and text:
                sid = await state["create"](self._service, text)

            payload[state["issue_key"]] = sid
            display_name: str = text
            for item in state["ref_data"]:
                if item["id"] == sid:
                    display_name = item["name"]
                    break
            self._issue[state["issue_key"]] = display_name

        if not payload:
            self._header_section.exit_edit_mode(saved=False)
            self._specs_grid.exit_edit_mode(saved=False)
            self._editing = False
            self._safe_update()
            return

        response = await self._service.update_issue(self._issue["id"], payload)

        if response and response.status_code in (200, 202):
            self._issue["name"] = name_value
            self._issue["market_value_mnh"] = str(mint_val)
            self._issue["market_value_used"] = str(used_val)
            self._issue["total_printed"] = str(total_val)
            self._issue["description"] = desc_val
            self._issue["note"] = notes_val
            self._issue["date"] = date_val
            self._header_section.exit_edit_mode(saved=True, new_name=name_value)
            self._specs_grid.exit_edit_mode(saved=True)
            await self.show_notification(_("issues.update_success"), Severity.SUCCESS)
            if self._on_edit_issue:
                self._on_edit_issue(self._issue["id"])
        else:
            await self.show_notification(_("issues.save_error_unknown"), Severity.ERROR)
            self._header_section.exit_edit_mode(saved=False)
            self._specs_grid.exit_edit_mode(saved=False)
        self._editing = False
        self._safe_update()

    async def _handle_cancel_edit(self, e: ft.ControlEvent) -> None:
        self._header_section.exit_edit_mode(saved=False)
        self._specs_grid.exit_edit_mode(saved=False)
        self._editing = False
        self._safe_update()

    # --- Delete issue dialog ---

    def _handle_delete_issue(self, e: ft.ControlEvent) -> None:
        issue_id = self._issue.get("id")
        issue_name: str = self._issue.get("name") or _("ui.no_text_value")
        if issue_id is None:
            return

        def confirm_action(_: ft.ControlEvent) -> None:
            dlg.open = False
            self.page.update()
            if self._on_delete_issue:
                self._on_delete_issue(issue_id)

        def cancel_action(_: ft.ControlEvent) -> None:
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("issues.delete_confirm"), font_family="Roboto-Bold"),
            content=ft.Column(
                controls=[
                    ft.Text(_("issues.delete_confirm_message"), font_family="Roboto"),
                    ft.Container(height=10),
                    ft.Text(f"{_('issues.name')}: {issue_name}", size=14, color=ft.Colors.GREY_700),
                ],
                spacing=4,
                tight=True,
            ),
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            actions=[
                DefaultButton(_("ui.cancel").upper(), on_click=cancel_action),
                AlertButton(_("ui.delete").upper(), on_click=confirm_action),
            ],
            actions_alignment="end",
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    # --- Add stamp ---

    def _handle_add_stamp(self, e: ft.ControlEvent) -> None:
        issue_id = self._issue.get("id")
        if self._on_add_stamp and issue_id is not None:
            self._on_add_stamp(issue_id)
