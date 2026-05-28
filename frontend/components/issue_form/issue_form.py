import datetime
from typing import Any, Callable, Optional

import flet as ft
import requests

from components.buttons.default_button import DefaultButton
from components.buttons.primary_button import PrimaryButton
from components.colors import GREY_700
from components.constants import (
    CARD_BORDER_RADIUS,
    CARD_ELEVATION,
    CARD_PADDING,
    DIALOG_WIDTH,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL_HEADING,
    STANDARD_PADDING,
)
from components.form.dropdown import Dropdown
from components.form.text_field import TextField
from components.table.column_def import fmt_date
from core.translations import _, get_language


from core.base_ui import BaseUI
from core.severity import Severity
from core.logger import Logger
from services.issue_service import IssueService


class IssueForm(BaseUI, Logger):
    """AlertDialog-based form for creating a new stamp issue.

    Fetches reference data (countries, artists, stamp types, etc.) on
    open, provides a specs grid matching the IssueDetailCard layout,
    and submits via ``IssueService.create_issue`` on confirmation.

    Reference data fields are editable Dropdown components whose
    popup menu is anchored below via MenuStyle.  Users can type
    free text or select from existing options.

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
        """Initialize the form with page, service, and success callback.

        Args:
            page: The Flet page instance.
            issue_service: IssueService for API calls.
            on_success: Called after the issue is created and dialog closes.
                This callback is invoked synchronously (not awaited). If you
                need async behaviour, wrap with ``page.run_task(...)``.
        """
        super().__init__()
        self.page: ft.Page = page
        self._service: IssueService = issue_service
        self._on_success: Optional[Callable[[], None]] = on_success

        self._dlg: Optional[ft.AlertDialog] = None

        # Reference data (populated by _fetch_reference_data)
        self._countries: list[dict] = []
        self._artists: list[dict] = []
        self._stamp_types: list[dict] = []
        self._paper_types: list[dict] = []
        self._print_types: list[dict] = []
        self._printers: list[dict] = []
        self._years: list[dict] = []

        # Form field controls
        self._name_field: Optional[ft.TextField] = None
        self._name_label: Optional[ft.Text] = None
        self._date_label: Optional[ft.Text] = None
        self._country_dropdown: Optional[Dropdown] = None
        self._artist_dropdown: Optional[Dropdown] = None
        self._stamp_type_dropdown: Optional[Dropdown] = None
        self._perforation_field: Optional[ft.TextField] = None
        self._paper_type_dropdown: Optional[Dropdown] = None
        self._printer_dropdown: Optional[Dropdown] = None
        self._print_type_dropdown: Optional[Dropdown] = None
        self._description_field: Optional[ft.TextField] = None
        self._notes_field: Optional[ft.TextField] = None
        self._mint_field: Optional[ft.TextField] = None
        self._used_field: Optional[ft.TextField] = None
        self._total_printed_field: Optional[ft.TextField] = None

        self._selected_date: Optional[datetime.date] = None

    # --- Helpers ---

    def _get_today(self) -> str:
        return fmt_date(datetime.date.today().isoformat(), lang=get_language())

    @staticmethod
    def _build_dropdown(items: list[dict]) -> Dropdown:
        """Build an editable reference-data dropdown from a list of items.

        Args:
            items: List of ``{"id": int, "name": str}`` dicts.

        Returns:
            A Dropdown with options for each item, editable for free-text entry.
        """
        return Dropdown(
            label=None,
            options=[
                ft.dropdown.Option(text=i["name"], key=str(i["id"]))
                for i in items
            ],
            editable=True,
            expand=True,
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT),
            enable_filter=True,
            border_width=1,
            focused_border_width=1,
        )

    @staticmethod
    def _paired_cell(icon: str, label: str, control: ft.Control) -> ft.Container:
        """Build a labelled form cell with icon, uppercase label, and control.

        Args:
            icon: The Flet icon name (e.g. ``ft.Icons.FLAG``).
            label: The display label (auto-uppercased).
            control: The input control below the label.

        Returns:
            A Container with label text + icon+control row.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        label.upper(),
                        font_family="Roboto-Black",
                        size=FONT_SIZE_DEFAULT,
                        color=GREY_700,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=18, color=GREY_700),
                            control,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                ],
                spacing=4,
            ),
            expand=True,
        )

    # --- Lifecycle ---

    async def show(self) -> None:
        """Fetch reference data and display the form dialog."""
        self._date_picker = ft.DatePicker(
            on_change=self._on_date_picker_change,
        )
        self.page.overlay.append(self._date_picker)

        self._dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("issues.add_title"), font_family="Roboto-Bold", margin=ft.Margin(left=24)),
            content=self._build_loading_view(),
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        )
        self.page.overlay.append(self._dlg)
        self._dlg.open = True
        self.page.update()

        await self._fetch_reference_data()
        self._build_form()
        self.page.update()

    def close(self) -> None:
        """Close the dialog and clean up."""
        if self._dlg:
            self._dlg.open = False
            self.page.update()

    # --- Loading view ---

    def _build_loading_view(self) -> ft.Column:
        """Show a loading spinner while reference data is fetched.

        Returns:
            A Column with centered ProgressRing and loading text.
        """
        return ft.Column(
            controls=[
                ft.Container(height=20),
                ft.Row(
                    controls=[ft.ProgressRing()],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=10),
                ft.Row(
                    controls=[
                        ft.Text(
                            _("ui.loading"),
                            size=FONT_SIZE_DEFAULT,
                            color=GREY_700,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=20),
            ],
            width=DIALOG_WIDTH,
            height=400,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # --- Reference data ---

    async def _fetch_reference_data(self) -> None:
        """Fetch all dropdown data from backend APIs in parallel."""
        import asyncio

        tasks: list = [
            self._get_data(self._service.get_countries()),
            self._get_data(self._service.get_artists()),
            self._get_data(self._service.get_stamp_types()),
            self._get_data(self._service.get_paper_types()),
            self._get_data(self._service.get_print_types()),
            self._get_data(self._service.get_printers()),
            self._service.get_years(),
        ]
        results = await asyncio.gather(*tasks)
        (
            self._countries,
            self._artists,
            self._stamp_types,
            self._paper_types,
            self._print_types,
            self._printers,
            years_response,
        ) = results

        if years_response and hasattr(years_response, 'status_code') and years_response.status_code == requests.codes.ok:
            try:
                self._years = years_response.json().get("data", [])
            except Exception:
                self._years = []
        else:
            self._years = []

    @staticmethod
    async def _get_data(coro: Any) -> list[dict]:
        """Await a coroutine that returns list[dict], defaulting to [].

        Args:
            coro: An awaitable that should return list[dict].

        Returns:
            The result or [] on any error.
        """
        try:
            return await coro
        except Exception:
            return []

    # --- Form assembly ---

    def _build_form(self) -> None:
        """Build the form content and replace the loading view."""
        name_section = self._build_name_section()
        date_row = self._build_date_row()
        specs_grid = self._build_specs_grid()
        description, notes = self._build_notes_section()
        actions = self._build_actions()
        form_card = self._assemble_card(name_section, date_row, specs_grid, description, notes)

        form_column = ft.Column(
            controls=[
                form_card,
                ft.Container(height=STANDARD_PADDING),
                actions,
            ],
            scroll=ft.ScrollMode.AUTO,
            width=DIALOG_WIDTH,
        )

        if self._dlg:
            self._dlg.content = form_column
            self._dlg.title = ft.Text(_("issues.add_title"), font_family="Roboto-Bold", margin=ft.Margin(left=12))
            self._dlg.actions = None

    def _build_name_section(self) -> tuple[ft.Text, TextField]:
        """Build the issue name label and input field.

        Returns:
            Tuple of (label, TextField) for the issue name.
        """
        self._name_label = ft.Text(
            _("issues.name").upper(),
            font_family="Roboto-Black",
            size=FONT_SIZE_DEFAULT,
            color=GREY_700,
        )
        self._name_field = TextField(
            expand=True,
            border_width=1,
            focused_border_width=1,
        )
        return self._name_label, self._name_field

    def _build_date_row(self) -> ft.Row:
        """Build the date picker row and numeric value fields (mint/used/total).

        Returns:
            A Row containing date display, mint value, and used value cells.
        """
        self._date_label = ft.Text(
            self._get_today(),
            size=FONT_SIZE_SMALL_HEADING,
            color=GREY_700,
        )
        date_icon_btn = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            icon_size=20,
            icon_color=GREY_700,
            on_click=self._on_date_icon_click,
        )

        self._mint_field = TextField(
            label=None,
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            border_width=1,
            focused_border_width=1,
        )
        self._used_field = TextField(
            label=None,
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            border_width=1,
            focused_border_width=1,
        )
        self._total_printed_field = TextField(
            label=None,
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            border_width=1,
            focused_border_width=1,
        )

        self._date_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[self._date_label, date_icon_btn],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                ),
                self._paired_cell(ft.Icons.MONETIZATION_ON, _("stamps.mint"), self._mint_field),
                self._paired_cell(ft.Icons.PAYMENT, _("stamps.used"), self._used_field),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return self._date_row

    def _build_specs_grid(self) -> list[ft.Row]:
        """Build the 4-row specs grid (country/stamp_type, perforation/total, artist/paper, printer/print_type).

        Returns:
            A list of 4 Rows, each containing two paired cells.
        """
        self._country_dropdown = self._build_dropdown(self._countries)
        self._stamp_type_dropdown = self._build_dropdown(self._stamp_types)
        self._perforation_field = TextField(label=None)
        self._artist_dropdown = self._build_dropdown(self._artists)
        self._paper_type_dropdown = self._build_dropdown(self._paper_types)
        self._printer_dropdown = self._build_dropdown(self._printers)
        self._print_type_dropdown = self._build_dropdown(self._print_types)

        pair_1 = ft.Row(
            controls=[
                self._paired_cell(ft.Icons.FLAG, _("issues.country"), self._country_dropdown),
                self._paired_cell(ft.Icons.CATEGORY, _("stamps.stamp_type"), self._stamp_type_dropdown),
            ],
            spacing=16,
        )
        pair_2 = ft.Row(
            controls=[
                self._paired_cell(ft.Icons.GRID_ON, _("issues.perforation"), self._perforation_field),
                self._paired_cell(ft.Icons.NUMBERS, _("stamps.total_printed"), self._total_printed_field),
            ],
            spacing=16,
        )
        pair_3 = ft.Row(
            controls=[
                self._paired_cell(ft.Icons.BRUSH, _("issues.artist"), self._artist_dropdown),
                self._paired_cell(ft.Icons.TEXT_SNIPPET, _("issues.paper_type"), self._paper_type_dropdown),
            ],
            spacing=16,
        )
        pair_4 = ft.Row(
            controls=[
                self._paired_cell(ft.Icons.FACTORY, _("issues.printer"), self._printer_dropdown),
                self._paired_cell(ft.Icons.PRINT, _("issues.print_type"), self._print_type_dropdown),
            ],
            spacing=16,
        )
        return [pair_1, pair_2, pair_3, pair_4]

    def _build_notes_section(self) -> tuple[TextField, TextField]:
        """Build the multiline description and notes text fields.

        Returns:
            Tuple of (description_field, notes_field).
        """
        self._description_field = TextField(
            label=None,
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_width=1,
            focused_border_width=1,
        )
        self._notes_field = TextField(
            label=None,
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_width=1,
            focused_border_width=1,
        )
        return self._description_field, self._notes_field

    def _build_actions(self) -> ft.Row:
        """Build the Cancel and Create buttons row.

        Returns:
            A Row with Cancel (DefaultButton) and Create (PrimaryButton).
        """
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
        return ft.Row(
            controls=[cancel_btn, create_btn],
            alignment=ft.MainAxisAlignment.END,
            spacing=12,
        )

    def _assemble_card(
        self,
        name_section: tuple[ft.Text, TextField],
        date_row: ft.Row,
        specs_grid: list[ft.Row],
        description: TextField,
        notes: TextField,
    ) -> ft.Card:
        """Assemble all form sections into a single Card layout.

        Args:
            name_section: (label, field) tuple from _build_name_section.
            date_row: The date/value row from _build_date_row.
            specs_grid: The 4-row specs grid from _build_specs_grid.
            description: The description TextField.
            notes: The notes TextField.

        Returns:
            A Card containing the full form layout.
        """
        name_label, name_field = name_section
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(content=name_label),
                        ft.Container(height=4),
                        name_field,
                        ft.Container(height=16),
                        date_row,
                        ft.Container(height=16),
                        specs_grid[0],
                        ft.Container(height=8),
                        specs_grid[1],
                        ft.Container(height=8),
                        specs_grid[2],
                        ft.Container(height=8),
                        specs_grid[3],
                        ft.Container(height=16),
                        self._paired_cell(ft.Icons.DESCRIPTION, _("stamps.description"), description),
                        ft.Container(height=16),
                        self._paired_cell(ft.Icons.NOTE, _("stamps.notes"), notes),
                    ],
                    spacing=0,
                ),
                padding=CARD_PADDING,
            ),
            elevation=CARD_ELEVATION,
        )

    # --- Event handlers ---

    def _on_date_icon_click(self, e: ft.ControlEvent) -> None:
        """Open the DatePicker when the calendar icon is clicked.

        Args:
            e: The click event from the calendar icon button.
        """
        if self._date_picker:
            self._date_picker.open = True
            self.page.update()

    def _on_date_picker_change(self, e: ft.ControlEvent) -> None:
        """Update the date label when a date is selected.

        Args:
            e: The DatePicker change event with the selected date.
        """
        raw = e.control.value if e.control else None
        if raw is None:
            return
        dt: datetime.date = raw.date() if isinstance(raw, datetime.datetime) else raw

        self._selected_date = dt
        self._date_label.value = fmt_date(dt.isoformat(), get_language())
        self.page.update()

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
        name_val = self._name_field.value.strip() if self._name_field and self._name_field.value else ""
        if not name_val:
            await self.show_notification(_("issues.name_required"), severity=Severity.ERROR)
            return

        try:
            mint_val = float(self._mint_field.value) if self._mint_field and self._mint_field.value else None
        except ValueError:
            await self.show_notification(_("issues.invalid_mnh"), severity=Severity.ERROR)
            return

        try:
            used_val = float(self._used_field.value) if self._used_field and self._used_field.value else None
        except ValueError:
            await self.show_notification(_("issues.invalid_used"), severity=Severity.ERROR)
            return

        try:
            total_printed_val = int(self._total_printed_field.value) if self._total_printed_field and self._total_printed_field.value else None
        except ValueError:
            await self.show_notification(_("issues.invalid_total_printed"), severity=Severity.ERROR)
            return

        async def _resolve_ref(dropdown: ft.Dropdown | None, create_func) -> int | None:
            val = dropdown.value
            if val is None:
                new_ref = dropdown.text
                self.log.debug(f"Creating new reference data: {new_ref}")
                new_id = await create_func(new_ref)
                if new_id is None:
                    await self.show_notification(_("issues.creation_failed"), severity=Severity.ERROR)
                return new_id
            return int(val)

        self.log.debug("Resolving reference data...")
        country_id = await _resolve_ref(self._country_dropdown, self._service.create_country)
        artist_id = await _resolve_ref(self._artist_dropdown, self._service.create_artist)
        stamp_type_id = await _resolve_ref(self._stamp_type_dropdown, self._service.create_stamp_type)
        paper_type_id = await _resolve_ref(self._paper_type_dropdown, self._service.create_paper_type)
        printer_id = await _resolve_ref(self._printer_dropdown, self._service.create_printer)
        print_type_id = await _resolve_ref(self._print_type_dropdown, self._service.create_print_type)

        year_number = (self._selected_date or datetime.date.today()).year
        year_id = None
        for year_obj in self._years:
            if year_obj.get("year") == year_number:
                year_id = year_obj.get("id")
                self.log.debug(f" Found year match: {year_id}: {year_number}")
                break

        if year_id is None:
            self.log.debug(f" Year {year_number} not found in cache, creating new one")
            year_id = await self._service.create_year(year_number)
            if year_id is None:
                self.log.error(f"Failed to create year {year_number}")
                await self.show_notification(_("issues.creation_failed"), severity=Severity.ERROR)
                return

        payload: dict[str, Any] = {
            "name": name_val,
            "country": country_id,
            "artist": artist_id,
            "stamp_type": stamp_type_id,
            "paper_type": paper_type_id,
            "printer": printer_id,
            "print_type": print_type_id,
            "year": year_id,
            "date": (self._selected_date or datetime.date.today()).isoformat()
        }
        self.log.debug(f"Payload built: {payload}")

        if self._perforation_field and self._perforation_field.value:
            payload["perforation"] = self._perforation_field.value.strip()
        if mint_val is not None:
            payload["market_value_mnh"] = mint_val
        if used_val is not None:
            payload["market_value_used"] = used_val
        if total_printed_val is not None:
            payload["total_printed"] = total_printed_val
        if self._description_field and self._description_field.value:
            payload["description"] = self._description_field.value.strip()
        if self._notes_field and self._notes_field.value:
            payload["note"] = self._notes_field.value.strip()

        self.log.debug(f"About to call create_issue with payload: {payload}")
        try:
            response = await self._service.create_issue(payload)
            self.log.debug(f"create_issue returned: {response}")
            if response and response.status_code in (200, 201):
                self.close()
                if self._on_success:
                    self._on_success()
                await self.show_notification(_("issues.creation_success"), severity=Severity.SUCCESS)
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
        except Exception as e:
            self.log.error(f"{e}")
            await self.show_notification(_("issues.network_error"), severity=Severity.ERROR)
