"""Unit tests for issue_detail/ — IssueHeaderSection, IssueSpecsGrid, IssueStampGrid, IssueDetailCard."""

from unittest.mock import ANY, MagicMock, PropertyMock, patch

import pytest
import flet as ft

from components.table.issue_detail.issue_detail_card import IssueDetailCard
from components.table.issue_detail.issue_header_section import IssueHeaderSection
from components.table.issue_detail.issue_specs_grid import IssueSpecsGrid
from components.table.issue_detail.issue_stamp_grid import IssueStampGrid
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


# ==============================================================================
# IssueHeaderSection
# ==============================================================================

class TestIssueHeaderSection:
    """IssueHeaderSection — identity header with name, badges, and icons."""

    def _header(self, issue: dict) -> IssueHeaderSection:
        return IssueHeaderSection(
            issue=issue,
            lang="en",
            on_edit_click=MagicMock(),
            on_delete_click=MagicMock(),
            on_save_click=MagicMock(),
            on_cancel_click=MagicMock(),
        )

    def test_contains_issue_name(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        name_text = h.content.controls[0].controls[0].content
        assert name_text.value == "Marianne Series"
        assert name_text.size == 32

    def test_contains_date(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        date_text = h.content.controls[1].content
        assert "2023" in date_text.value

    def test_has_edit_icon(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        action_row = h.content.controls[0].controls[2]
        assert action_row.controls[0].icon == ft.Icons.EDIT
        assert action_row.controls[0].tooltip is not None

    def test_has_delete_icon(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        action_row = h.content.controls[0].controls[2]
        assert action_row.controls[3].icon == ft.Icons.DELETE
        assert action_row.controls[3].tooltip is not None

    def test_valuation_badges(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        badges_row = h.content.controls[0].controls[1]
        assert len(badges_row.controls) == 5

    def test_name_fallback_when_missing(self) -> None:
        issue: dict = {"id": 1, "date": "2023-01-01", "market_value_mnh": "0", "market_value_used": "0"}
        h = self._header(issue)
        name_text = h.content.controls[0].controls[0].content
        assert name_text.value is not None
        assert len(name_text.value) > 0

    def test_edit_mode_swaps_name_to_textfield(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        h.enter_edit_mode("Hint")
        assert isinstance(h.content.controls[0].controls[0].content, ft.TextField)
        assert not h._edit_icon.visible
        assert h._save_icon.visible

    def test_exit_edit_mode_restores_text(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        h.enter_edit_mode("Hint")
        h.exit_edit_mode(saved=True, new_name="New Name")
        name_text = h.content.controls[0].controls[0].content
        assert isinstance(name_text, ft.Text)
        assert name_text.value == "New Name"
        assert h._edit_icon.visible
        assert not h._save_icon.visible

    def test_exit_edit_mode_cancel_restores_original(self, sample_issue: dict) -> None:
        h = self._header(sample_issue)
        h.enter_edit_mode("Hint")
        h.exit_edit_mode(saved=False)
        name_text = h.content.controls[0].controls[0].content
        assert name_text.value == "Marianne Series"


# ==============================================================================
# IssueSpecsGrid
# ==============================================================================

class TestIssueSpecsGrid:
    """IssueSpecsGrid — technical specs grid with description/notes."""

    def test_returns_card(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        assert isinstance(grid, ft.Card)

    def test_has_eight_detail_cells(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        col_body = grid.content.content
        responsive_row = col_body.controls[0]
        assert len(responsive_row.controls) == 8

    def test_description_section(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        col_body = grid.content.content
        description_col = col_body.controls[2]
        assert len(description_col.controls) == 2

    def test_notes_section(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        col_body = grid.content.content
        notes_col = col_body.controls[3]
        assert len(notes_col.controls) == 2

    def test_has_divider(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        col_body = grid.content.content
        assert isinstance(col_body.controls[1], ft.Divider)

    def test_country_value(self, sample_issue: dict) -> None:
        grid = IssueSpecsGrid(issue=sample_issue)
        col_body = grid.content.content
        responsive_row = col_body.controls[0]
        country_cell = responsive_row.controls[0]
        value_container = country_cell.content.controls[1].controls[1]
        assert isinstance(value_container, ft.Container)
        assert isinstance(value_container.content, ft.Text)
        assert value_container.content.value == "France"


class TestIssueSpecsGridBuildCell:
    """_build_cell helper method."""

    def _cell(self, value: str = "France", col=None):
        grid = IssueSpecsGrid(issue={"name": "Test"})
        return grid._build_cell(ft.Icons.FLAG, "Country", value, col=col)

    def test_sets_col_property(self) -> None:
        cell = self._cell(col={"sm": 6, "md": 4})
        assert cell.col == {"sm": 6, "md": 4}

    def test_default_col(self) -> None:
        cell = self._cell()
        assert cell.col == 12

    def test_contains_icon_and_label_value(self) -> None:
        cell = self._cell()
        row = cell.content
        assert row.controls[0].content.icon == ft.Icons.FLAG
        assert row.controls[1].controls[0].value == "COUNTRY"
        value_container = row.controls[1].controls[1]
        assert isinstance(value_container, ft.Container)
        assert isinstance(value_container.content, ft.Text)
        assert value_container.content.value == "France"


# ==============================================================================
# IssueStampGrid
# ==============================================================================

class TestIssueStampGrid:
    """IssueStampGrid — loading, empty, and populated states."""

    _STAMP_PATCH = "components.table.issue_detail.issue_stamp_grid.StampCard"

    def test_loading_state(self, sample_issue: dict) -> None:
        with patch(self._STAMP_PATCH):
            grid = IssueStampGrid(stamps=[], loading=True, lang="en", issue_year="2023")
        text_control = grid.content.content
        assert text_control.value is not None
        assert len(text_control.value) > 0

    def test_empty_state(self, sample_issue: dict) -> None:
        with patch(self._STAMP_PATCH):
            grid = IssueStampGrid(stamps=[], loading=False, lang="en", issue_year="2023")
        text_control = grid.content.content
        assert text_control.value is not None
        assert len(text_control.value) > 0

    def test_populated_state_returns_responsive_row(self, sample_stamps: dict) -> None:
        with patch(self._STAMP_PATCH):
            grid = IssueStampGrid(stamps=sample_stamps, loading=False, lang="en", issue_year="2023")
        assert isinstance(grid.content, ft.ResponsiveRow)

    def test_stamps_sorted_by_fesofi_code(self, sample_stamps: dict) -> None:
        with patch(self._STAMP_PATCH) as mock_stamp:
            mock_stamp.side_effect = lambda stamp, **kw: MagicMock(stamp=stamp)
            grid = IssueStampGrid(stamps=sample_stamps, loading=False, lang="en", issue_year="2023")
        assert len(grid.content.controls) == 3

    def test_add_stamp_button_is_last_item(self, sample_stamps: dict) -> None:
        with patch(self._STAMP_PATCH):
            grid = IssueStampGrid(stamps=sample_stamps, loading=False, lang="en", issue_year="2023")
        last_item = grid.content.controls[-1]
        card_content = last_item.content
        assert card_content.content.controls[0].controls[0].icon == ft.Icons.ADD

    def test_stamp_card_created_with_correct_args(self, sample_issue: dict) -> None:
        stamps_wrapped = {"data": [{"name": "Stamp A", "fesofi_code": "FR001"}]}
        on_edit = MagicMock()
        on_delete = MagicMock()
        with patch(self._STAMP_PATCH) as mock_stamp:
            mock_stamp.return_value = MagicMock()
            grid = IssueStampGrid(
                stamps=stamps_wrapped, loading=False, lang="en", issue_year="2023",
                on_edit_stamp=on_edit, on_delete_stamp=on_delete,
            )
        mock_stamp.assert_called_once_with(
            stamp=stamps_wrapped["data"][0],
            issue_year="2023",
            lang="en",
            on_edit=on_edit,
            on_delete=on_delete,
        )


# ==============================================================================
# IssueDetailCard — coordinator
# ==============================================================================

class TestIssueDetailCardInit:
    """Construction and state storage."""

    CARD_PATCH = "components.table.issue_detail.issue_stamp_grid.StampCard"

    def _card(self, **kw) -> IssueDetailCard:
        defaults = dict(issue={"id": 1, "name": "T"}, stamps=[], lang="en")
        defaults.update(kw)
        with patch(self.CARD_PATCH):
            return IssueDetailCard(**defaults)

    def test_stores_issue_and_lang(self, sample_issue: dict) -> None:
        card = self._card(issue=sample_issue, stamps=[], lang="en")
        assert card._issue is sample_issue
        assert card._issue["name"] == "Marianne Series"

    def test_padding_and_bgcolor(self) -> None:
        card = self._card()
        assert card.padding == 20
        assert card.bgcolor == ft.Colors.BLUE_GREY_50

    def test_content_has_three_sections(self) -> None:
        card = self._card()
        column = card.content
        assert isinstance(column, ft.Column)
        assert len(column.controls) == 3

    def test_stores_callbacks(self) -> None:
        on_edit_issue = MagicMock()
        on_delete_issue = MagicMock()
        on_add_stamp = MagicMock()
        card = self._card(
            on_edit_issue=on_edit_issue,
            on_delete_issue=on_delete_issue,
            on_add_stamp=on_add_stamp,
        )
        assert card._on_edit_issue is on_edit_issue
        assert card._on_delete_issue is on_delete_issue
        assert card._on_add_stamp is on_add_stamp

    def test_default_callbacks_are_none(self) -> None:
        card = self._card()
        assert card._on_edit_issue is None
        assert card._on_delete_issue is None
        assert card._on_add_stamp is None


class TestIssueDetailCardHandlers:
    """Coordinator event handlers."""

    CARD_PATCH = "components.table.issue_detail.issue_stamp_grid.StampCard"

    def _card(self, **kw) -> IssueDetailCard:
        defaults = dict(issue={"id": 42, "name": "T"}, stamps=[], lang="en")
        defaults.update(kw)
        with patch(self.CARD_PATCH):
            return IssueDetailCard(**defaults)

    @pytest.mark.asyncio
    async def test_handle_edit_issue_noop_when_no_service(self, sample_issue: dict) -> None:
        card = self._card(issue=sample_issue, service=None)
        await card._handle_edit_issue(MagicMock())
        assert not card._editing

    @pytest.mark.asyncio
    async def test_handle_edit_issue_noop_when_already_editing(self, sample_issue: dict) -> None:
        service = MagicMock()
        card = self._card(issue=sample_issue, service=service)
        card._editing = True
        await card._handle_edit_issue(MagicMock())
        assert card._editing

    def test_handle_delete_issue_shows_dialog(self) -> None:
        callback = MagicMock()
        card = self._card(on_delete_issue=callback)
        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())
        mock_page.overlay.append.assert_called_once()
        dlg = mock_page.overlay.append.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)
        assert dlg.modal is True

    def test_handle_delete_issue_confirm_fires_callback(self) -> None:
        callback = MagicMock()
        card = self._card(on_delete_issue=callback)
        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())
            dlg = mock_page.overlay.append.call_args[0][0]
            confirm_btn = dlg.actions[1]
            confirm_btn.on_click(MagicMock())
        callback.assert_called_once_with(42)

    def test_handle_delete_issue_cancel_does_not_fire(self) -> None:
        callback = MagicMock()
        card = self._card(on_delete_issue=callback)
        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())
            dlg = mock_page.overlay.append.call_args[0][0]
            cancel_btn = dlg.actions[0]
            cancel_btn.on_click(MagicMock())
        callback.assert_not_called()

    def test_handle_delete_issue_noop_when_no_id(self) -> None:
        callback = MagicMock()
        card = self._card(issue={"name": "Test", "date": "2023-01-01"}, on_delete_issue=callback)
        card._handle_delete_issue(MagicMock())
        callback.assert_not_called()

    def test_handle_delete_issue_noop_when_no_callback(self) -> None:
        card = self._card()
        mock_page = MagicMock()
        with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
            card._handle_delete_issue(MagicMock())

    def test_handle_add_stamp_fires_callback(self) -> None:
        callback = MagicMock()
        card = self._card(on_add_stamp=callback)
        card._handle_add_stamp(MagicMock())
        callback.assert_called_once_with(42)

    def test_handle_add_stamp_noop_when_no_callback(self) -> None:
        card = self._card()
        card._handle_add_stamp(MagicMock())

    @pytest.mark.asyncio
    async def test_handle_cancel_edit_exits_edit_mode(self) -> None:
        card = self._card()
        card._editing = True
        await card._handle_cancel_edit(MagicMock())
        assert not card._editing
