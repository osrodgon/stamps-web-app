"""Unit tests for components/stamp_form/stamp_form.py — Create Stamp dialog."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import flet as ft
import requests

from components.form.dialogs.stamp_form import StampForm


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
    service.update_stamp = AsyncMock(return_value=None)
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
        assert form._name_field is not None
        assert form._fesofi_field is not None
        assert form._edifil_field is not None
        assert form._face_value_field is not None
        assert form._color_dropdown is not None
        assert form._color_chips is not None
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

    def test_resolve_no_colors_selected(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        assert form._resolve_color_ids() == []

    def test_resolve_with_selected_colors(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._selected_colors = [
            {"id": 1, "name": "Red"},
            {"id": 3, "name": "Green"},
        ]
        assert form._resolve_color_ids() == [1, 3]

    def test_resolve_removed_colors_excluded(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._selected_colors = [
            {"id": 1, "name": "Red"},
            {"id": 2, "name": "Blue"},
        ]
        form._selected_colors = [c for c in form._selected_colors if c["id"] != 1]
        assert form._resolve_color_ids() == [2]


class TestStampFormChips:
    """Tests for the inline color dropdown selector and chips."""

    def test_update_color_dropdown_filters_selected(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._color_dropdown = MagicMock()
        form._color_chips = MagicMock()
        form._selected_colors = [{"id": 1, "name": "Red"}]
        form._update_color_dropdown_and_chips(page_not_ready=True)

        options = form._color_dropdown.options
        assert len(options) == 2
        option_keys = [opt.key for opt in options]
        assert "1" not in option_keys
        assert "2" in option_keys
        assert "3" in option_keys

    def test_on_color_selected_adds_color(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._color_dropdown = MagicMock()
        form._color_chips = MagicMock()
        event = ft.ControlEvent(data="2", control=form._color_dropdown, name="select")
        form._on_color_selected(event)

        ids = [c["id"] for c in form._selected_colors]
        assert 2 in ids

    def test_remove_color_restores_option(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._color_dropdown = MagicMock()
        form._color_chips = MagicMock()
        form._selected_colors = [
            {"id": 1, "name": "Red"},
            {"id": 2, "name": "Blue"},
        ]
        form._remove_color(2)

        ids = [c["id"] for c in form._selected_colors]
        assert 2 not in ids
        assert 1 in ids

    def test_rebuild_chips_creates_correct_count(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._selected_colors = sample_colors_response.json.return_value["data"]
        form._color_chips = ft.Row()
        form._rebuild_chips(page_not_ready=True)
        controls = form._color_chips.controls
        assert len(controls) == 3
        assert isinstance(controls[0], ft.Chip)


class TestStampFormValidation:
    """Tests for form validation in _on_create."""

    async def test_missing_name_does_not_create(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._face_value_field.value = "1.00"
        await form._on_save(MagicMock())
        mock_service.create_stamp.assert_not_awaited()

    async def test_missing_face_value_does_not_create(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._name_field.value = "Test Stamp"
        await form._on_save(MagicMock())
        mock_service.create_stamp.assert_not_awaited()

    async def test_valid_fields_calls_create_stamp(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        mock_service.create_stamp = AsyncMock(return_value=response)

        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        await form.show()
        form._name_field.value = "Test Stamp"
        form._face_value_field.value = "1.00"
        await form._on_save(MagicMock())

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


class TestStampFormEditMode:
    """Tests for StampForm in edit mode (stamp_data provided)."""

    sample_stamp: dict = {
        "id": 99,
        "name": "My Stamp",
        "fesofi_code": "F123",
        "edifil_code": "E456",
        "face_value": "2.50",
        "market_value_mnh": "1.00",
        "market_value_used": "0.50",
        "total_printed": "10000",
        "description": "A test stamp",
        "colors": ["Red", "Blue"],
    }

    def test_init_edit_mode_stores_data(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42, stamp_data=self.sample_stamp)
        assert form._editing is True
        assert form._stamp_id == 99
        assert form._stamp_data is self.sample_stamp

    async def test_show_edit_mode_pre_populates_fields(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_colors = AsyncMock(return_value=sample_colors_response)
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42, stamp_data=self.sample_stamp)
        await form.show()
        assert form._name_field.value == "My Stamp"
        assert form._fesofi_field.value == "F123"
        assert form._edifil_field.value == "E456"
        assert form._face_value_field.value == "2.50"
        assert form._mnh_field.value == "1.00"
        assert form._used_field.value == "0.50"
        assert form._total_printed_field.value == "10000"
        assert form._description_field.value == "A test stamp"

    async def test_show_edit_mode_pre_populates_colors(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_colors = AsyncMock(return_value=sample_colors_response)
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42, stamp_data=self.sample_stamp)
        await form.show()
        selected_names: list[str] = [c["name"] for c in form._selected_colors]
        assert "Red" in selected_names
        assert "Blue" in selected_names
        assert "Green" not in selected_names

    async def test_edit_mode_calls_update_stamp(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        mock_service.update_stamp = AsyncMock(return_value=response)
        mock_service.get_colors = AsyncMock(return_value=None)

        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42, stamp_data=self.sample_stamp)
        await form.show()
        form._name_field.value = "Updated Stamp"
        form._face_value_field.value = "3.00"
        await form._on_save(MagicMock())

        mock_service.update_stamp.assert_awaited_once()
        args, _ = mock_service.update_stamp.call_args
        stamp_id, payload = args
        assert stamp_id == 99
        assert payload["name"] == "Updated Stamp"
        assert payload["face_value"] == "3.00"
        assert "issue" not in payload

    async def test_edit_omits_issue_from_payload(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        mock_service.update_stamp = AsyncMock(return_value=response)
        mock_service.get_colors = AsyncMock(return_value=None)

        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42, stamp_data=self.sample_stamp)
        await form.show()
        form._name_field.value = "Test"
        form._face_value_field.value = "1.00"
        await form._on_save(MagicMock())

        _, payload = mock_service.update_stamp.call_args[0]
        assert "issue" not in payload
