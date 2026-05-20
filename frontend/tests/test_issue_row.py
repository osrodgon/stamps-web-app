"""Unit tests for components/table/issue_row.py — single row with expandable details."""

from unittest.mock import MagicMock, patch

import pytest

from components.table.issue_row import IssueRow
from components.table.column_def import COLUMNS
from components.colors import BG_LIGHT, BG_ALT, TEXT_BLUE


@pytest.fixture
def sample_issue() -> dict:
    return {
        "id": 1,
        "country": "France",
        "date": "2023-06-15",
        "name": "Marianne Series",
        "artist": "Test Artist",
        "printer": "Test Printer",
        "perforation": "Zebra",
        "stamp_type": "Definitive",
        "print_type": "Lithography",
        "paper_type": "Glossy",
        "total_printed": 500000,
        "market_value_mnh": "1.20",
        "market_value_used": "0.80",
    }


class TestIssueRowBuild:
    """Tests for IssueRow construction and cell rendering."""

    def test_builds_correct_cell_count(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS)

        main_row = row.content.controls[0]
        assert len(main_row.content.controls) == len(COLUMNS) + 1

    def test_zebra_striping_even_row(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, row_index=0)

        assert row.bgcolor == BG_LIGHT

    def test_zebra_striping_odd_row(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, row_index=1)

        assert row.bgcolor == BG_ALT

    def test_name_column_has_blue_text(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS)

        main_row = row.content.controls[0]
        name_col_index = [c.api_key for c in COLUMNS].index("name") + 1
        name_cell = main_row.content.controls[name_col_index]
        name_text = name_cell.content
        assert name_text.color == TEXT_BLUE


class TestIssueRowExpand:
    """Tests for the expand/collapse behavior."""

    def test_toggle_expand_changes_visibility(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS)

        assert row._details.visible is False

        with patch.object(row, "update"):
            row._toggle_expand(None)

        assert row._details.visible is True

    def test_toggle_expand_changes_chevron(self, sample_issue: dict) -> None:
        import flet as ft

        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS)

        assert row._chevron_icon.icon == ft.Icons.KEYBOARD_ARROW_DOWN

        with patch.object(row, "update"):
            row._toggle_expand(None)

        assert row._chevron_icon.icon == ft.Icons.KEYBOARD_ARROW_UP

    def test_toggle_expand_calls_callback(self, sample_issue: dict) -> None:
        callback = MagicMock()

        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, on_expand=callback)

        with patch.object(row, "update"):
            row._toggle_expand(None)

        callback.assert_called_once_with(sample_issue["id"])

    def test_start_expanded(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, expanded=True)

        assert row._details.visible is True
        assert row._is_expanded is True


class TestIssueRowStamps:
    """Tests for stamp data updates."""

    def test_set_stamps_rebuilds_details(self, sample_issue: dict) -> None:
        stamps = {"data": [{"name": "Stamp 1"}, {"name": "Stamp 2"}]}

        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, expanded=True)

        with patch.object(row, "update"):
            row.set_stamps(stamps)

        assert row._stamps == stamps
        assert row._loading_stamps is False

    def test_set_loading_when_expanded(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, expanded=True)

        row.set_loading()

        assert row._loading_stamps is True

    def test_set_loading_noop_when_collapsed(self, sample_issue: dict) -> None:
        with patch("components.table.issue_row.IssueDetailCard"), \
             patch.object(IssueRow, "update"):
            row = IssueRow(issue=sample_issue, columns=COLUMNS, expanded=False)

        row.set_loading()

        assert row._loading_stamps is False
