"""Unit tests for pages/admin/stamps_manager_page.py — stamps catalog admin page.

Only static methods and handler stubs are tested here. Full page
instantiation is deferred due to Flet's C++ Prop descriptor system
(same limitation as auth card tests).
"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from pages.admin.stamps_manager_page import StampsManagerPage


class TestRoundDown:
    """Tests for the _round_down static method."""

    def test_round_down_exact_multiple(self) -> None:
        assert StampsManagerPage._round_down(1840) == 1840

    def test_round_down_rounds_down(self) -> None:
        assert StampsManagerPage._round_down(1852) == 1850

    def test_round_down_rounds_down_2(self) -> None:
        assert StampsManagerPage._round_down(1857) == 1855

    def test_round_down_zero(self) -> None:
        assert StampsManagerPage._round_down(0) == 0

    def test_round_down_negative(self) -> None:
        assert StampsManagerPage._round_down(-1) == -5


class TestRoundUp:
    """Tests for the _round_up static method."""

    def test_round_up_exact_multiple(self) -> None:
        assert StampsManagerPage._round_up(1840) == 1840

    def test_round_up_rounds_up(self) -> None:
        assert StampsManagerPage._round_up(1852) == 1855

    def test_round_up_rounds_up_2(self) -> None:
        assert StampsManagerPage._round_up(1857) == 1860

    def test_round_up_zero(self) -> None:
        assert StampsManagerPage._round_up(0) == 0

    def test_round_up_negative(self) -> None:
        assert StampsManagerPage._round_up(-1) == 0


class TestHandlerStubs:
    """Tests for handler stub methods using direct __init__ bypass."""

    def _make_manager(self) -> StampsManagerPage:
        with patch.object(StampsManagerPage, "__init__", return_value=None):
            m = StampsManagerPage.__new__(StampsManagerPage)
            m._log = MagicMock()
            return m

    def test_handle_edit_stamp_logs(self) -> None:
        m = self._make_manager()
        m._handle_edit_stamp(1)
        m._log.debug.assert_called_once_with("Edit stamp 1")

    def test_handle_delete_stamp_logs_and_runs_task(self) -> None:
        # PropertyMock needed because ``page`` is a read-only C++ Prop
        # (Flet descriptor) — patching it directly would fail.
        m = self._make_manager()
        mock_page = MagicMock()
        with patch.object(type(m), "page", new_callable=PropertyMock, return_value=mock_page):
            m._handle_delete_stamp(2, 5)
        m._log.debug.assert_called_once_with("Delete stamp 2 from issue 5")
        mock_page.run_task.assert_called_once()

    def test_handle_edit_issue_logs(self) -> None:
        m = self._make_manager()
        m._handle_edit_issue(3)
        m._log.debug.assert_called_once_with("Edit issue 3")

    def test_handle_delete_issue_logs_and_runs_task(self) -> None:
        m = self._make_manager()
        mock_page = MagicMock()
        with patch.object(type(m), "page", new_callable=PropertyMock, return_value=mock_page):
            m._handle_delete_issue(4)
        m._log.debug.assert_called_once_with("Delete issue 4")
        mock_page.run_task.assert_called_once()

    def test_handle_add_stamp_logs(self) -> None:
        m = self._make_manager()
        m._handle_add_stamp(5)
        m._log.debug.assert_called_once_with("Add stamp to issue 5")
