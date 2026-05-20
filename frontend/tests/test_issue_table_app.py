"""Unit tests for components/table/issue_table_app.py — main issue table with state management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components.table.issue_table_app import IssueTableApp
from components.table.column_def import COLUMNS
from services.issue_service import IssueService


class TestParseFilter:
    """Tests for the static _parse_filter method."""

    def test_parse_filter_empty(self) -> None:
        assert IssueTableApp._parse_filter("") == ("", "")

    def test_parse_filter_whitespace_only(self) -> None:
        assert IssueTableApp._parse_filter("   ") == ("", "")

    def test_parse_filter_year_only(self) -> None:
        assert IssueTableApp._parse_filter("2002") == ("", "2002")

    def test_parse_filter_year_wildcard(self) -> None:
        assert IssueTableApp._parse_filter("19*") == ("", "1900-1999")

    def test_parse_filter_year_wildcard_2digit(self) -> None:
        assert IssueTableApp._parse_filter("200*") == ("", "2000-2009")

    def test_parse_filter_name(self) -> None:
        assert IssueTableApp._parse_filter("Marianne") == ("Marianne", "")

    def test_parse_filter_whitespace(self) -> None:
        assert IssueTableApp._parse_filter("  Marianne  ") == ("Marianne", "")

    def test_parse_filter_mixed_text(self) -> None:
        assert IssueTableApp._parse_filter("Series 2023") == ("Series 2023", "")


class TestIssueTableAppState:
    """Tests for initial state and configuration."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        service = MagicMock(spec=IssueService)
        service.get_issues = AsyncMock(return_value=None)
        service.get_issue_stamps = AsyncMock(return_value=MagicMock(ok=True, json=lambda: {"data": []}))
        return service

    @pytest.fixture
    def app(self, mock_service: MagicMock) -> IssueTableApp:
        with patch("components.table.issue_table_app.TableHeader"), \
             patch("components.table.issue_table_app.TablePagination"):
            return IssueTableApp(service=mock_service)

    def test_initial_state_defaults(self, app: IssueTableApp) -> None:
        assert app._current_page == 1
        assert app._rows_per_page == 15
        assert app._sort_key == "date"
        assert app._sort_order == "asc"
        assert app._name_filter == ""

    def test_initial_data_empty(self, app: IssueTableApp) -> None:
        assert app._data == []
        assert app._total == 0


class TestIssueTableAppFilters:
    """Tests for filter and sort state changes."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        service = MagicMock(spec=IssueService)
        service.get_issues = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def app(self, mock_service: MagicMock) -> IssueTableApp:
        with patch("components.table.issue_table_app.TableHeader"), \
             patch("components.table.issue_table_app.TablePagination"):
            app = IssueTableApp(service=mock_service)
        return app

    def test_set_year_filter_resets_page(self, app: IssueTableApp) -> None:
        app._current_page = 3
        with patch.object(app, "_schedule_fetch"):
            app.set_year_filter("1900-2000")

        assert app._current_page == 1
        assert app._year_filter == "1900-2000"

    def test_on_sort_resets_page(self, app: IssueTableApp) -> None:
        app._current_page = 4
        with patch.object(app, "_schedule_fetch"):
            app._on_sort("name", "desc")

        assert app._current_page == 1
        assert app._sort_key == "name"
        assert app._sort_order == "desc"

    def test_on_page_change_updates_page(self, app: IssueTableApp) -> None:
        with patch.object(app, "_schedule_fetch"):
            app._on_page_change(5)

        assert app._current_page == 5

    def test_on_page_size_change_resets_page(self, app: IssueTableApp) -> None:
        app._current_page = 3
        with patch.object(app, "_schedule_fetch"):
            app._on_page_size_change(50)

        assert app._current_page == 1
        assert app._rows_per_page == 50


class TestIssueTableAppRebuildRows:
    """Tests for the _rebuild_rows method."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        service = MagicMock(spec=IssueService)
        service.get_issues = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def app(self, mock_service: MagicMock) -> IssueTableApp:
        with patch("components.table.issue_table_app.TableHeader"), \
             patch("components.table.issue_table_app.TablePagination"):
            app = IssueTableApp(service=mock_service)
        return app

    def test_rebuild_rows_empty_shows_empty_text(self, app: IssueTableApp) -> None:
        app._data = []
        with patch.object(app, "update"):
            app._rebuild_rows()

        assert app._empty_text.visible is True
        assert len(app._rows_container.controls) == 0

    def test_rebuild_rows_populated_creates_rows(self, app: IssueTableApp) -> None:
        app._data = [
            {"id": 1, "name": "Issue 1", "country": "France"},
            {"id": 2, "name": "Issue 2", "country": "Spain"},
        ]
        with patch("components.table.issue_table_app.IssueRow") as mock_row, \
             patch.object(app, "update"):
            mock_row.return_value = MagicMock()
            app._rebuild_rows()

        assert app._empty_text.visible is False
        assert mock_row.call_count == 2

    def test_rebuild_rows_auto_expands_single_row(self, app: IssueTableApp) -> None:
        app._data = [{"id": 1, "name": "Issue 1", "country": "France"}]
        app._rows_per_page = 1

        with patch("components.table.issue_table_app.IssueRow") as mock_row, \
             patch.object(app, "_on_expand"), \
             patch.object(app, "update"):
            mock_instance = MagicMock()
            mock_row.return_value = mock_instance
            app._rebuild_rows()

            call_kwargs = mock_row.call_args[1]
            assert call_kwargs["expanded"] is True
            app._on_expand.assert_called_once_with(1)
