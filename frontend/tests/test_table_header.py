"""Unit tests for components/table/table_header.py — column header with sort controls."""

from unittest.mock import MagicMock, patch

import pytest

from components.table.table_header import TableHeader
from components.table.column_def import COLUMNS


class TestTableHeaderBuild:
    """Tests for header construction from COLUMNS definition."""

    def test_builds_correct_column_count(self) -> None:
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS)

        assert len(header.content.controls) == len(COLUMNS) + 1

    def test_first_cell_is_spacer(self) -> None:
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS)

        assert header.content.controls[0].width == 24

    def test_default_sort_key_and_order(self) -> None:
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS)

        assert header._sort_key == "date"
        assert header._sort_order == "asc"


class TestSortableColumns:
    """Tests for sortable column behavior."""

    @pytest.fixture
    def header(self) -> TableHeader:
        with patch.object(TableHeader, "update"):
            return TableHeader(columns=COLUMNS, sort_key="date", sort_order="asc")

    def test_sortable_columns_have_click_handlers(self, header: TableHeader) -> None:
        sortable_cells = [
            ctrl for ctrl in header.content.controls[1:]
            if ctrl.on_click is not None
        ]
        sortable_defs = [col for col in COLUMNS if col.sortable]

        assert len(sortable_cells) == len(sortable_defs)

    def test_non_sortable_columns_no_click(self, header: TableHeader) -> None:
        non_sortable_cells = [
            ctrl for ctrl in header.content.controls[1:]
            if ctrl.on_click is None
        ]
        non_sortable_defs = [col for col in COLUMNS if not col.sortable]

        assert len(non_sortable_cells) == len(non_sortable_defs)

    def test_active_sort_column_shows_icon(self, header: TableHeader) -> None:
        date_cell = None
        for ctrl in header.content.controls[1:]:
            if hasattr(ctrl, "on_click") and ctrl.on_click is not None:
                inner_row = ctrl.content
                if isinstance(inner_row, type(header.content)):
                    for inner_ctrl in inner_row.controls:
                        if hasattr(inner_ctrl, "visible") and inner_ctrl.visible:
                            date_cell = ctrl
                            break

        assert date_cell is not None

    def test_toggle_sort_reverses_order(self, header: TableHeader) -> None:
        with patch.object(header, "update"):
            header._toggle_sort("date")

        assert header._sort_order == "desc"

    def test_toggle_sort_changes_key(self, header: TableHeader) -> None:
        with patch.object(header, "update"):
            header._toggle_sort("name")

        assert header._sort_key == "name"
        assert header._sort_order == "asc"

    def test_toggle_sort_calls_callback(self, header: TableHeader) -> None:
        callback = MagicMock()
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS, sort_key="date", sort_order="asc", on_sort=callback)

        with patch.object(header, "update"):
            header._toggle_sort("date")

        callback.assert_called_once_with("date", "desc")


class TestUpdateSortIndicators:
    """Tests for the update_sort_indicators method."""

    def test_update_sort_indicators_syncs_state(self) -> None:
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS, sort_key="date", sort_order="asc")

        with patch.object(header, "update"):
            header.update_sort_indicators("name", "desc")

        assert header._sort_key == "name"
        assert header._sort_order == "desc"

    def test_update_sort_indicators_rebuilds(self) -> None:
        with patch.object(TableHeader, "update"):
            header = TableHeader(columns=COLUMNS, sort_key="date", sort_order="asc")

        original_content = header.content

        with patch.object(header, "update"):
            header.update_sort_indicators("name", "desc")

        assert header.content is not original_content
