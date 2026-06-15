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
        assert form._select_colors_btn is not None
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
    """Tests for the chip-based color selector via picker dialog."""

    def test_show_color_picker_creates_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._show_color_picker()
        assert form._color_dialog is not None
        assert form._color_dialog.open is True
        assert len(form._color_checkboxes) == 3

    def test_show_color_picker_pre_checks_selected(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._selected_colors = [{"id": 1, "name": "Red"}]
        form._show_color_picker()
        red_cb = [cb for cb in form._color_checkboxes if cb.label == "Red"][0]
        blue_cb = [cb for cb in form._color_checkboxes if cb.label == "Blue"][0]
        assert red_cb.value is True
        assert blue_cb.value is False

    def test_apply_colors_saves_checked(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._color_chips = MagicMock()
        form._show_color_picker()
        form._color_checkboxes[0].value = True   # Blue (id=2)
        form._color_checkboxes[1].value = True   # Green (id=3)
        form._color_checkboxes[2].value = False  # Red (id=1) unchecked
        form._apply_colors()
        ids = [c["id"] for c in form._selected_colors]
        assert 2 in ids  # Blue
        assert 3 in ids  # Green
        assert 1 not in ids  # Red unchecked

    def test_apply_colors_empty_when_none_checked(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._colors_list = sample_colors_response.json.return_value["data"]
        form._color_chips = MagicMock()
        form._show_color_picker()
        for cb in form._color_checkboxes:
            cb.value = False
        form._apply_colors()
        assert form._selected_colors == []

    def test_remove_color_removes_from_list(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._selected_colors = [
            {"id": 1, "name": "Red"},
            {"id": 2, "name": "Blue"},
            {"id": 3, "name": "Green"},
        ]
        form._color_chips = MagicMock()
        form._remove_color(2)
        assert form._selected_colors == [{"id": 1, "name": "Red"}, {"id": 3, "name": "Green"}]

    def test_rebuild_chips_creates_correct_count(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = StampForm(page=mock_page, issue_service=mock_service, issue_id=42)
        form._selected_colors = sample_colors_response.json.return_value["data"]
        form._color_chips = MagicMock()
        form._rebuild_chips()
        controls = form._color_chips.controls
        assert len(controls) == 3
        assert isinstance(controls[0], ft.Chip)


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
