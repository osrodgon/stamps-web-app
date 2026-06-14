"""Unit tests for components/stamp_form/stamp_form.py — Create Stamp dialog."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import flet as ft
import requests

from components.stamp_form.stamp_form import StampForm


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock(spec=ft.Page)
    page.overlay = []
    page.show_dialog = MagicMock()
    return page


@pytest.fixture
def mock_service() -> MagicMock:
    service = MagicMock()
    service.get_colors = AsyncMock(return_value=None)
    service.create_stamp = AsyncMock(return_value=None)
    return service


sample_colors_response: MagicMock = MagicMock(spec=requests.Response)
sample_colors_response.status_code = 200
sample_colors_response.json.return_value = {
    "data": [
        {"id": 1, "name": "Red"},
        {"id": 2, "name": "Blue"},
        {"id": 3, "name": "Green"},
    ]
}


class TestStampFormInit:
    """Tests for StampForm initialization."""

    def test_init_stores_references(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(
            page=mock_page,
            issue_service=mock_service,
            issue_id=42,
            on_success=lambda: None,
        )
        assert form.page is mock_page
        assert form._service is mock_service
        assert form._issue_id == 42
        assert form._on_success is not None
        assert form._dlg is None


class TestStampFormShow:
    """Tests for the show() method."""

    async def test_show_creates_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        assert form._dlg is not None
        assert form._dlg in mock_page.overlay
        assert form._dlg.open is True

    async def test_show_fetches_colors(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        mock_service.get_colors.assert_awaited_once()

    async def test_show_stores_colors(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_colors = AsyncMock(return_value=sample_colors_response)
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        assert len(form._colors_list) == 3

    async def test_show_builds_content(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        assert form._dlg.content is not None

    async def test_show_sets_field_references(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        assert form._name_field is not None
        assert form._fesofi_field is not None
        assert form._edifil_field is not None
        assert form._face_value_field is not None
        assert form._colors_field is not None
        assert form._mnh_field is not None
        assert form._used_field is not None
        assert form._total_printed_field is not None
        assert form._description_field is not None


class TestStampFormCancel:
    """Tests for the cancel action."""

    async def test_cancel_closes_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._on_cancel(MagicMock())
        assert form._dlg.open is False


class TestStampFormResolveColors:
    """Tests for _resolve_color_ids."""

    def test_resolve_exact_names(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        ids = form._resolve_color_ids("Red, Blue, Green")
        assert ids == [1, 2, 3]

    def test_resolve_with_whitespace(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        ids = form._resolve_color_ids("  Red ,  Blue  ")
        assert ids == [1, 2]

    def test_resolve_empty_string(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        assert form._resolve_color_ids("") == []

    def test_resolve_unknown_name_skipped(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        ids = form._resolve_color_ids("Red, Purple, Blue")
        assert ids == [1, 2]

    def test_resolve_no_colors(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = []
        assert form._resolve_color_ids("Red, Blue") == []


class TestStampFormValidation:
    """Tests for form validation in _on_create."""

    async def test_missing_name_does_not_create(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._face_value_field.value = "1.00"
        await form._on_create(MagicMock())
        mock_service.create_stamp.assert_not_awaited()

    async def test_missing_face_value_does_not_create(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._name_field.value = "Test Stamp"
        await form._on_create(MagicMock())
        mock_service.create_stamp.assert_not_awaited()

    async def test_valid_fields_calls_create_stamp(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        mock_service.create_stamp = AsyncMock(return_value=response)

        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._name_field.value = "Test Stamp"
        form._face_value_field.value = "1.00"
        await form._on_create(MagicMock())

        mock_service.create_stamp.assert_awaited_once()
        args, _ = mock_service.create_stamp.call_args
        payload = args[0]
        assert payload["issue"] == 42
        assert payload["name"] == "Test Stamp"
        assert payload["face_value"] == "1.00"


class TestStampFormClose:
    """Tests for close()."""

    async def test_close_closes_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form.close()
        assert form._dlg.open is False
