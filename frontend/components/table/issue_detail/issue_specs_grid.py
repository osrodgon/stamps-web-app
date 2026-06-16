"""Technical specs grid with edit mode support."""

import asyncio
from typing import Any, Callable, Optional

import flet as ft

from components.colors import GREY_700
from components.form.auto_complete_field import AutoCompleteField
from core.translations import _
from components.constants import (
    CARD_ELEVATION,
    FONT_SIZE_DEFAULT,
)
from services.issue_service import IssueService


_EDITABLE_FIELDS: dict[str, dict[str, Any]] = {
    "country": {
        "icon": ft.Icons.FLAG,
        "label_key": "common.country",
        "issue_key": "country",
        "fetch": lambda s: s.get_countries(),
        "create": lambda s, n: s.create_country(n),
        "hint": "issues.hint_country",
    },
    "stamp_type": {
        "icon": ft.Icons.CATEGORY,
        "label_key": "common.stamp_type",
        "issue_key": "stamp_type",
        "fetch": lambda s: s.get_stamp_types(),
        "create": lambda s, n: s.create_stamp_type(n),
        "hint": "issues.hint_stamp_type",
    },
    "printer": {
        "icon": ft.Icons.FACTORY,
        "label_key": "common.printer",
        "issue_key": "printer",
        "fetch": lambda s: s.get_printers(),
        "create": lambda s, n: s.create_printer(n),
        "hint": "issues.hint_printer_type",
    },
    "print_type": {
        "icon": ft.Icons.PRINT,
        "label_key": "common.print_type",
        "issue_key": "print_type",
        "fetch": lambda s: s.get_print_types(),
        "create": lambda s, n: s.create_print_type(n),
        "hint": "issues.hint_print_type",
    },
    "artist": {
        "icon": ft.Icons.BRUSH,
        "label_key": "common.artist",
        "issue_key": "artist",
        "fetch": lambda s: s.get_artists(),
        "create": lambda s, n: s.create_artist(n),
        "hint": "issues.hint_artist",
    },
    "paper_type": {
        "icon": ft.Icons.DESCRIPTION,
        "label_key": "common.paper_type",
        "issue_key": "paper_type",
        "fetch": lambda s: s.get_paper_types(),
        "create": lambda s, n: s.create_paper_type(n),
        "hint": "issues.hint_paper_type",
    },
}


class IssueSpecsGrid(ft.Card):
    """Technical specifications grid with inline edit mode.

    Renders a responsive grid of eight attribute cells (country, stamp_type,
    printer, year, perforation, print_type, artist, paper_type) followed by
    a divider, description section, and notes section.

    Edit mode swaps editable cells to ``AutoCompleteField`` widgets,
    driven by the ``_EDITABLE_FIELDS`` module-level dict.

    Args:
        issue: Issue data dict.
    """

    def __init__(self, issue: dict) -> None:
        super().__init__()
        self._issue: dict = issue
        self._detail_cells: dict[str, ft.Container] = {}
        self._edit_state: dict[str, dict[str, Any]] = {}
        self._description_container: Optional[ft.Container] = None
        self._notes_container: Optional[ft.Container] = None
        self._description_textfield: Optional[ft.TextField] = None
        self._notes_textfield: Optional[ft.TextField] = None
        self._original_description: str = issue.get("description") or ""
        self._original_notes: str = issue.get("note") or ""
        self._perforation_cell: Optional[ft.Container] = None
        self._perforation_textfield: Optional[ft.TextField] = None
        self._original_perforation: str = issue.get("perforation") or ""

        self.elevation = CARD_ELEVATION
        self.content = self._build_content()

    def _build_cell(self, icon: str, label: str, value: str, col: Optional[dict] = None) -> ft.Container:
        container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Icon(icon, size=18, color=GREY_700), width=18),
                    ft.Column(
                        controls=[
                            ft.Text(
                                label.upper(),
                                size=FONT_SIZE_DEFAULT,
                                font_family="Roboto-Black",
                                color=GREY_700,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    value,
                                    size=FONT_SIZE_DEFAULT,
                                    font_family="Roboto",
                                ),
                                height=20,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        if col:
            container.col = col
        return container

    def _build_content(self) -> ft.Container:
        issue = self._issue
        description: str = issue.get("description") or _("ui.no_text_value")
        notes: str = issue.get("note") or _("ui.no_text_value")

        self._detail_cells = {}
        for key, field in _EDITABLE_FIELDS.items():
            self._detail_cells[key] = self._build_cell(
                field["icon"],
                _(field["label_key"]),
                issue.get(field["issue_key"]) or "-",
                col={"sm": 6, "md": 4},
            )

        self._perforation_cell = self._build_cell(
            ft.Icons.GRID_ON, _("common.perforation"),
            issue.get("perforation") or "-",
            col={"sm": 6, "md": 4},
        )

        self._description_container = ft.Container(
            content=ft.Text(
                str(description),
                size=FONT_SIZE_DEFAULT,
                font_family="Roboto",
                text_align=ft.TextAlign.JUSTIFY,
            ),
        )
        self._notes_container = ft.Container(
            content=ft.Text(
                str(notes),
                size=FONT_SIZE_DEFAULT,
                font_family="Roboto",
                text_align=ft.TextAlign.JUSTIFY,
            ),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            self._detail_cells["country"],
                            self._detail_cells["stamp_type"],
                            self._detail_cells["printer"],
                            self._build_cell(ft.Icons.CALENDAR_TODAY, _("stamps.year"), issue.get("year") or "-", col={"sm": 6, "md": 4}),
                            self._perforation_cell,
                            self._detail_cells["print_type"],
                            self._detail_cells["artist"],
                            self._detail_cells["paper_type"],
                        ],
                        run_spacing=8,
                    ),
                    ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                    ft.Column(
                        controls=[
                            ft.Text(
                                _("common.description").upper(),
                                size=FONT_SIZE_DEFAULT,
                                font_family="Roboto-Black",
                                color=GREY_700,
                            ),
                            self._description_container,
                        ],
                        spacing=4,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                _("common.notes").upper(),
                                size=FONT_SIZE_DEFAULT,
                                font_family="Roboto-Black",
                                color=GREY_700,
                            ),
                            self._notes_container,
                        ],
                        spacing=4,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
        )

    # --- Edit mode ---

    async def enter_edit_mode(self, service: IssueService) -> bool:
        """Fetch reference data and swap editable cells to AutoCompleteFields.

        Returns:
            True if edit mode entered successfully, False on fetch failure.
        """
        try:
            coros = [field["fetch"](service) for field in _EDITABLE_FIELDS.values()]
            results = await asyncio.gather(*coros)
            ref_data = dict(zip(_EDITABLE_FIELDS.keys(), results))
        except Exception:
            return False

        self._edit_state = {}
        for key, field in _EDITABLE_FIELDS.items():
            current_value: str = self._issue.get(field["issue_key"]) or ""
            ac = AutoCompleteField(items=ref_data[key], expand=True, hint_text=_(field["hint"]))
            ac.margin = ft.Margin(0, -14, 0, 0)
            if current_value:
                ac.set_text(current_value)

            cell = self._detail_cells[key]
            value_container: ft.Container = cell.content.controls[1].controls[1]
            value_container.content = ac

            self._edit_state[key] = {
                "ac": ac,
                "original": current_value,
                "ref_data": ref_data[key],
                "issue_key": field["issue_key"],
                "create": field["create"],
            }

        self._description_textfield = ft.TextField(
            value=self._issue.get("description") or self._original_description,
            multiline=True,
            min_lines=2,
            max_lines=6,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto"),
        )
        self._description_container.content = self._description_textfield

        self._notes_textfield = ft.TextField(
            value=self._issue.get("note") or self._original_notes,
            multiline=True,
            min_lines=2,
            max_lines=6,
            border=ft.InputBorder.UNDERLINE,
            expand=True,
            dense=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto"),
        )
        self._notes_container.content = self._notes_textfield

        perf_val: str = self._issue.get("perforation") or ""
        self._perforation_textfield = ft.TextField(
            value=perf_val,
            border=ft.InputBorder.UNDERLINE,
            dense=True,
            expand=True,
            text_style=ft.TextStyle(size=FONT_SIZE_DEFAULT, font_family="Roboto"),
        )
        if self._perforation_cell:
            value_container: ft.Container = self._perforation_cell.content.controls[1].controls[1]
            value_container.content = self._perforation_textfield

        return True

    def exit_edit_mode(self, saved: bool) -> None:
        """Restore all editable cells to read-only display."""
        for key, state in self._edit_state.items():
            display_value: str = self._issue.get(state["issue_key"]) or "-"
            if not saved:
                display_value = state["original"] or "-"

            cell = self._detail_cells[key]
            value_container: ft.Container = cell.content.controls[1].controls[1]
            value_container.content = ft.Text(
                display_value,
                size=FONT_SIZE_DEFAULT,
                font_family="Roboto",
            )
        self._edit_state = {}

        if saved:
            desc_display: str = self._issue.get("description")
            if desc_display is None:
                desc_display = self._original_description
        else:
            desc_display = self._original_description
        self._description_container.content = ft.Text(
            desc_display,
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto",
            text_align=ft.TextAlign.JUSTIFY,
        )
        self._description_textfield = None

        if saved:
            notes_display: str = self._issue.get("note")
            if notes_display is None:
                notes_display = self._original_notes
        else:
            notes_display = self._original_notes
        self._notes_container.content = ft.Text(
            notes_display,
            size=FONT_SIZE_DEFAULT,
            font_family="Roboto",
            text_align=ft.TextAlign.JUSTIFY,
        )
        self._notes_textfield = None

        self._perforation_textfield = None
        perf_display: str = self._issue.get("perforation") or "-"
        if self._perforation_cell:
            value_container: ft.Container = self._perforation_cell.content.controls[1].controls[1]
            value_container.content = ft.Text(
                perf_display,
                size=FONT_SIZE_DEFAULT,
                font_family="Roboto",
            )

    @property
    def edit_state(self) -> dict[str, dict[str, Any]]:
        return self._edit_state

    @property
    def description_value(self) -> str:
        if self._description_textfield is not None:
            return self._description_textfield.value.strip()
        return self._original_description

    @property
    def notes_value(self) -> str:
        if self._notes_textfield is not None:
            return self._notes_textfield.value.strip()
        return self._original_notes

    @property
    def perforation_value(self) -> str:
        if self._perforation_textfield is not None:
            return self._perforation_textfield.value.strip()
        return self._original_perforation
