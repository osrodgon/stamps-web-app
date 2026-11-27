"""Unit tests for components/form/date_picker.py — DatePickerField."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
import flet as ft

from components.form.date_picker import DatePickerField
from components.form.text_field import APP_HEADER, DEFAULT, FieldStyle
from core.translations import get_language, set_language


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock(spec=ft.Page)
    page.overlay = []
    return page


class TestDatePickerFieldInit:
    """Tests for DatePickerField initialization."""

    def test_init_default_state(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        assert field._selected_date is None
        assert field.value is None
        assert field.label == "Date"
        assert field.read_only is True
        assert field._picker is not None

    def test_init_with_value(self, mock_page: MagicMock) -> None:
        field = DatePickerField(
            page=mock_page,
            label="Date",
            value=datetime.date(2024, 6, 15),
        )
        assert field._selected_date == datetime.date(2024, 6, 15)
        assert field.value == datetime.date(2024, 6, 15)

    def test_init_on_change_callback(self, mock_page: MagicMock) -> None:
        callback = MagicMock()
        field = DatePickerField(
            page=mock_page,
            label="Date",
            on_change=callback,
        )
        assert field._on_change_callback is callback

    def test_init_with_field_style(self, mock_page: MagicMock) -> None:
        field = DatePickerField(
            page=mock_page,
            label="Date",
            field_style=APP_HEADER,
        )
        assert field.border_color == APP_HEADER.border_color

    def test_init_appends_picker_to_overlay(self, mock_page: MagicMock) -> None:
        DatePickerField(page=mock_page, label="Date")
        assert len(mock_page.overlay) == 1

    def test_init_stores_page_reference(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        assert field._page is mock_page


class TestDatePickerFieldValue:
    """Tests for the value property."""

    def test_getter_returns_none_by_default(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        assert field.value is None

    def test_setter_updates_selected_date(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        field.value = datetime.date(2024, 12, 25)
        assert field.value == datetime.date(2024, 12, 25)
        assert field._selected_date == datetime.date(2024, 12, 25)

    def test_setter_clears_on_none(self, mock_page: MagicMock) -> None:
        field = DatePickerField(
            page=mock_page,
            label="Date",
            value=datetime.date(2024, 1, 1),
        )
        field.value = None
        assert field.value is None
        assert field._selected_date is None


class TestDatePickerFieldSetToday:
    """Tests for set_today()."""

    def test_set_today_sets_value(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        expected: datetime.date = datetime.date(2026, 5, 15)
        with patch("components.form.date_picker.get_local_today", return_value=expected):
            field.set_today()
        assert field.value == expected

    def test_set_today_fires_callback(self, mock_page: MagicMock) -> None:
        callback = MagicMock()
        field = DatePickerField(page=mock_page, label="Date", on_change=callback)
        expected: datetime.date = datetime.date(2026, 5, 15)
        with patch("components.form.date_picker.get_local_today", return_value=expected):
            field.set_today()
        callback.assert_called_once_with(expected)


class TestDatePickerFieldPicker:
    """Tests for internal DatePicker interaction."""

    def test_on_field_click_opens_picker(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        field._on_field_click(MagicMock())
        mock_page.show_dialog.assert_called_once_with(field._picker)

    async def test_on_picker_change_updates_value(self, mock_page: MagicMock) -> None:
        field = DatePickerField(page=mock_page, label="Date")
        mock_event = MagicMock()
        mock_event.control.value = datetime.datetime(2024, 6, 15, 22, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("components.form.date_picker._read_client_timezone", return_value="America/New_York"):
            await field._on_picker_change(mock_event)
        assert field.value == datetime.date(2024, 6, 15)
        mock_page.update.assert_called_once()

    async def test_on_picker_change_fires_callback(self, mock_page: MagicMock) -> None:
        callback = MagicMock()
        field = DatePickerField(page=mock_page, label="Date", on_change=callback)
        mock_event = MagicMock()
        mock_event.control.value = datetime.date(2024, 3, 20)
        with patch("components.form.date_picker._read_client_timezone", return_value="UTC"):
            await field._on_picker_change(mock_event)
        callback.assert_called_once_with(datetime.date(2024, 3, 20))

    async def test_on_picker_change_no_control(self, mock_page: MagicMock) -> None:
        callback = MagicMock()
        field = DatePickerField(page=mock_page, label="Date", on_change=callback)
        mock_event = MagicMock()
        mock_event.control = None
        with patch("components.form.date_picker._read_client_timezone", return_value="UTC"):
            await field._on_picker_change(mock_event)
        callback.assert_not_called()
