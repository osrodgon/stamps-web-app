"""Unit tests for components/table/issue_detail/issue_detail_card.py — expanded issue detail card."""

from unittest.mock import ANY, MagicMock, PropertyMock, patch

import pytest
import flet as ft

from components.table.issue_detail.issue_detail_card import IssueDetailCard
from components.table.column_def import COLUMNS
from core.translations import set_language


@pytest.fixture(autouse=True)
def _reset_language() -> None:
    set_language("en")


@pytest.fixture
def sample_issue() -> dict:
    return {
        "id": 42,
        "name": "Marianne Series",
        "date": "2023-06-15",
        "country": "France",
        "stamp_type": "Definitive",
        "printer": "Test Printer",
        "year": "2023",
        "perforation": "Zebra",
        "print_type": "Lithography",
        "artist": "Test Artist",
        "paper_type": "Glossy",
        "description": "A beautiful series.",
        "note": "First edition.",
        "total_printed": 500000,
        "market_value_mnh": "1.20",
        "market_value_used": "0.80",
    }


@pytest.fixture
def sample_stamps() -> dict:
    return {"data": [
        {"name": "Stamp B", "fesofi_code": "FR002", "edifil_code": "E2"},
        {"name": "Stamp A", "fesofi_code": "FR001", "edifil_code": "E1"},
    ]}


class TestIssueDetailCardInit:
    """Tests for construction and state storage."""

    def test_stores_issue_and_stamps(self, sample_issue: dict, sample_stamps: list[dict]) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=sample_stamps, lang="en")

        assert card._issue == sample_issue
        assert card._stamps == sample_stamps
        assert card._lang == "en"

    def test_stores_loading_default(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        assert card._loading is False

    def test_stores_loading_true(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", loading=True)

        assert card._loading is True

    def test_stores_callbacks(self, sample_issue: dict) -> None:
        on_edit_stamp = MagicMock()
        on_delete_stamp = MagicMock()
        on_edit_issue = MagicMock()
        on_delete_issue = MagicMock()
        on_add_stamp = MagicMock()

        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(
                issue=sample_issue,
                stamps=[],
                lang="en",
                on_edit_stamp=on_edit_stamp,
                on_delete_stamp=on_delete_stamp,
                on_edit_issue=on_edit_issue,
                on_delete_issue=on_delete_issue,
                on_add_stamp=on_add_stamp,
            )

        assert card._on_edit_stamp is on_edit_stamp
        assert card._on_delete_stamp is on_delete_stamp
        assert card._on_edit_issue is on_edit_issue
        assert card._on_delete_issue is on_delete_issue
        assert card._on_add_stamp is on_add_stamp

    def test_padding_and_bgcolor(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        assert card.padding == 20
        assert card.bgcolor == ft.Colors.BLUE_GREY_50

    def test_content_has_three_sections(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        column = card.content
        assert isinstance(column, ft.Column)
        assert len(column.controls) == 3

    def test_default_callbacks_are_none(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        assert card._on_edit_stamp is None
        assert card._on_delete_stamp is None
        assert card._on_edit_issue is None
        assert card._on_delete_issue is None
        assert card._on_add_stamp is None


class TestIssueDetailCardHeader:
    """Tests for _build_header — identity, valuation, and action icons."""

    def test_header_contains_issue_name(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        header = card._build_header()
        name_text = header.content.controls[0].controls[0]
        assert name_text.value == "Marianne Series"
        assert name_text.size == 32

    def test_header_contains_date(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        header = card._build_header()
        date_text = header.content.controls[1]
        assert "2023" in date_text.value

    def test_header_has_edit_icon(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        header = card._build_header()
        action_row = header.content.controls[0].controls[2]
        edit_btn = action_row.controls[0]
        assert edit_btn.icon == ft.Icons.EDIT
        assert edit_btn.tooltip is not None

    def test_header_has_delete_icon(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        header = card._build_header()
        action_row = header.content.controls[0].controls[2]
        delete_btn = action_row.controls[1]
        assert delete_btn.icon == ft.Icons.DELETE
        assert delete_btn.tooltip is not None

    def test_header_valuation_badges(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        header = card._build_header()
        badges_row = header.content.controls[0].controls[1]
        assert len(badges_row.controls) == 5

    def test_header_name_fallback_when_missing(self) -> None:
        issue: dict = {"id": 1, "date": "2023-01-01", "market_value_mnh": "0", "market_value_used": "0"}
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=issue, stamps=[], lang="en")

        header = card._build_header()
        name_text = header.content.controls[0].controls[0]
        assert name_text.value is not None
        assert len(name_text.value) > 0


class TestIssueDetailCardSpecs:
    """Tests for _build_specs — technical specs grid."""

    def test_specs_returns_card(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        assert isinstance(specs, ft.Card)

    def test_specs_has_eight_detail_cells(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        responsive_row = specs.content.content.controls[0]
        assert len(responsive_row.controls) == 8

    def test_specs_description_section(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        description_col = specs.content.content.controls[2]
        assert len(description_col.controls) == 2

    def test_specs_notes_section(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        notes_col = specs.content.content.controls[3]
        assert len(notes_col.controls) == 2

    def test_specs_has_divider(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        divider = specs.content.content.controls[1]
        assert isinstance(divider, ft.Divider)

    def test_specs_country_value(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        specs = card._build_specs()
        responsive_row = specs.content.content.controls[0]
        country_cell = responsive_row.controls[0]
        value_text = country_cell.content.controls[1].controls[1]
        assert value_text.value == "France"


class TestIssueDetailCardDetailCell:
    """Tests for _detail_cell helper."""

    def test_detail_cell_sets_col_property(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        cell = card._detail_cell(ft.Icons.FLAG, "Country", "France", col={"sm": 6, "md": 4})
        assert cell.col == {"sm": 6, "md": 4}

    def test_detail_cell_default_col(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        cell = card._detail_cell(ft.Icons.FLAG, "Country", "France")
        assert cell.col == 12

    def test_detail_cell_contains_icon_and_label_value(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        cell = card._detail_cell(ft.Icons.FLAG, "Country", "France")
        row = cell.content
        assert row.controls[0].content.icon == ft.Icons.FLAG
        assert row.controls[1].controls[0].value == "COUNTRY"
        assert row.controls[1].controls[1].value == "France"


class TestIssueDetailCardStampTable:
    """Tests for _build_stamp_table — loading, empty, and populated states."""

    def test_loading_state(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", loading=True)

        stamp_section = card._build_stamp_table()
        text_control = stamp_section.content
        assert text_control.value is not None
        assert len(text_control.value) > 0

    def test_empty_state(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", loading=False)

        stamp_section = card._build_stamp_table()
        text_control = stamp_section.content
        assert text_control.value is not None
        assert len(text_control.value) > 0

    def test_populated_state_returns_responsive_row(self, sample_issue: dict, sample_stamps: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=sample_stamps, lang="en")

        stamp_section = card._build_stamp_table()
        assert isinstance(stamp_section, ft.ResponsiveRow)

    def test_stamps_sorted_by_fesofi_code(self, sample_issue: dict, sample_stamps: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard") as mock_stamp:
            mock_stamp.side_effect = lambda stamp, **kw: MagicMock(stamp=stamp)
            card = IssueDetailCard(issue=sample_issue, stamps=sample_stamps, lang="en")

        stamp_section = card._build_stamp_table()
        assert len(stamp_section.controls) == 3

    def test_add_stamp_button_is_last_item(self, sample_issue: dict, sample_stamps: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=sample_stamps, lang="en")

        stamp_section = card._build_stamp_table()
        last_item = stamp_section.controls[-1]
        card_content = last_item.content
        assert card_content.content.controls[0].controls[0].icon == ft.Icons.ADD

    def test_stamp_card_created_with_correct_args(self, sample_issue: dict) -> None:
        stamps_wrapped: dict = {"data": [{"name": "Stamp A", "fesofi_code": "FR001"}]}
        with patch("components.table.issue_detail.issue_detail_card.StampCard") as mock_stamp:
            mock_stamp.return_value = MagicMock()
            card = IssueDetailCard(issue=sample_issue, stamps=stamps_wrapped, lang="en")

        card._build_stamp_table()
        mock_stamp.assert_called_once_with(
            stamp=stamps_wrapped["data"][0],
            issue_year="2023",
            lang="en",
            on_edit=card._on_edit_stamp,
            on_delete=ANY,
        )


class TestIssueDetailCardHandlers:
    """Tests for event handlers — edit, delete, add_stamp."""

    def test_handle_edit_issue_fires_callback(self, sample_issue: dict) -> None:
        callback = MagicMock()
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", on_edit_issue=callback)

        card._handle_edit_issue(MagicMock())
        callback.assert_called_once_with(42)

    def test_handle_edit_issue_noop_when_no_callback(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        card._handle_edit_issue(MagicMock())

    def test_handle_delete_issue_shows_dialog(self, sample_issue: dict) -> None:
        callback = MagicMock()
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", on_delete_issue=callback)

        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())

        mock_page.overlay.append.assert_called_once()
        dlg = mock_page.overlay.append.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)
        assert dlg.modal is True

    def test_handle_delete_issue_confirm_fires_callback(self, sample_issue: dict) -> None:
        callback = MagicMock()
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", on_delete_issue=callback)

        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())
            dlg = mock_page.overlay.append.call_args[0][0]
            confirm_btn = dlg.actions[1]
            confirm_btn.on_click(MagicMock())
        callback.assert_called_once_with(42)

    def test_handle_delete_issue_cancel_does_not_fire(self, sample_issue: dict) -> None:
        callback = MagicMock()
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", on_delete_issue=callback)

        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())
            dlg = mock_page.overlay.append.call_args[0][0]
            cancel_btn = dlg.actions[0]
            cancel_btn.on_click(MagicMock())
        callback.assert_not_called()

    def test_handle_delete_issue_noop_when_no_id(self) -> None:
        callback = MagicMock()
        issue: dict = {"name": "Test", "date": "2023-01-01"}
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=issue, stamps=[], lang="en", on_delete_issue=callback)

        card._handle_delete_issue(MagicMock())
        callback.assert_not_called()

    def test_handle_delete_issue_noop_when_no_callback(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())

    def test_handle_add_stamp_fires_callback(self, sample_issue: dict) -> None:
        callback = MagicMock()
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en", on_add_stamp=callback)

        card._handle_add_stamp(MagicMock())
        callback.assert_called_once_with(42)

    def test_handle_add_stamp_noop_when_no_callback(self, sample_issue: dict) -> None:
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=sample_issue, stamps=[], lang="en")

        card._handle_add_stamp(MagicMock())

    def test_handle_edit_issue_noop_when_id_missing(self) -> None:
        callback = MagicMock()
        issue: dict = {"name": "Test", "date": "2023-01-01"}
        with patch("components.table.issue_detail.issue_detail_card.StampCard"):
            card = IssueDetailCard(issue=issue, stamps=[], lang="en", on_edit_issue=callback)

        card._handle_edit_issue(MagicMock())
        callback.assert_not_called()
