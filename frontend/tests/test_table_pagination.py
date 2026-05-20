"""Unit tests for components/table/table_pagination.py — pagination controls."""

from unittest.mock import MagicMock, patch

import pytest

from components.table.table_pagination import TablePagination
from core.translations import set_language


class TestFormatRange:
    """Tests for the _format_range method."""

    def test_format_range_basic(self) -> None:
        set_language("en")
        pagination = TablePagination(page=1, page_size=15, total=65)

        assert pagination._format_range() == "1-15 of 65"

    def test_format_range_page_2(self) -> None:
        set_language("en")
        pagination = TablePagination(page=2, page_size=15, total=65)

        assert pagination._format_range() == "16-30 of 65"

    def test_format_range_last_partial_page(self) -> None:
        set_language("en")
        pagination = TablePagination(page=5, page_size=15, total=65)

        assert pagination._format_range() == "61-65 of 65"

    def test_format_range_zero_total(self) -> None:
        set_language("en")
        pagination = TablePagination(page=1, page_size=15, total=0)

        assert pagination._format_range() == "0 of 0"

    def test_format_range_exact_multiple(self) -> None:
        set_language("en")
        pagination = TablePagination(page=4, page_size=15, total=60)

        assert pagination._format_range() == "46-60 of 60"

    def test_format_range_locale_es(self) -> None:
        set_language("es")
        pagination = TablePagination(page=1, page_size=15, total=65)

        result = pagination._format_range()
        assert "1" in result
        assert "15" in result
        assert "65" in result


class TestTotalPages:
    """Tests for the _total_pages method."""

    def test_total_pages_basic(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)

        assert pagination._total_pages() == 5

    def test_total_pages_zero(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=0)

        assert pagination._total_pages() == 0

    def test_total_pages_exact_multiple(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=60)

        assert pagination._total_pages() == 4

    def test_total_pages_single_item(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=1)

        assert pagination._total_pages() == 1


class TestNavButtonStates:
    """Tests for navigation button enable/disable logic."""

    def test_first_button_disabled_on_page_1(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)
        pagination._update_nav_buttons()

        assert pagination._first_btn.disabled is True
        assert pagination._prev_btn.disabled is True

    def test_last_button_disabled_on_final_page(self) -> None:
        pagination = TablePagination(page=5, page_size=15, total=65)
        pagination._update_nav_buttons()

        assert pagination._next_btn.disabled is True
        assert pagination._last_btn.disabled is True

    def test_middle_page_all_buttons_enabled(self) -> None:
        pagination = TablePagination(page=3, page_size=15, total=65)
        pagination._update_nav_buttons()

        assert pagination._first_btn.disabled is False
        assert pagination._prev_btn.disabled is False
        assert pagination._next_btn.disabled is False
        assert pagination._last_btn.disabled is False

    def test_single_page_all_buttons_disabled(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=10)
        pagination._update_nav_buttons()

        assert pagination._first_btn.disabled is True
        assert pagination._prev_btn.disabled is True
        assert pagination._next_btn.disabled is True
        assert pagination._last_btn.disabled is True


class TestUpdateState:
    """Tests for the update_state method."""

    def test_update_state_changes_values(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)

        with patch.object(pagination, "update"):
            pagination.update_state(page=3, page_size=20, total=100)

        assert pagination._page == 3
        assert pagination._page_size == 20
        assert pagination._total == 100

    def test_update_state_updates_range_text(self) -> None:
        set_language("en")
        pagination = TablePagination(page=1, page_size=15, total=65)

        with patch.object(pagination, "update"):
            pagination.update_state(page=2, page_size=20, total=100)

        assert pagination._range_text.value == "21-40 of 100"

    def test_update_state_updates_dropdown_value(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)

        with patch.object(pagination, "update"):
            pagination.update_state(page=1, page_size=50, total=200)

        assert pagination._dropdown.value == "50"


class TestSetButtonState:
    """Tests for the _set_button_state helper."""

    def test_disable_button(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)
        btn = pagination._first_btn

        pagination._set_button_state(btn, True)

        assert btn.disabled is True

    def test_enable_button(self) -> None:
        pagination = TablePagination(page=1, page_size=15, total=65)
        btn = pagination._first_btn
        btn.disabled = True

        pagination._set_button_state(btn, False)

        assert btn.disabled is False
