"""Unit tests for components/issue_form/issue_form.py — Add Issue dialog."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import datetime
import pytest
import flet as ft
import requests

from components.issue_form.issue_form import IssueForm
from components.table.column_def import fmt_date
from core.translations import _, get_language


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock(spec=ft.Page)
    page.overlay = []
    page.show_dialog = MagicMock()
    return page


@pytest.fixture
def mock_service() -> MagicMock:
    service = MagicMock()
    service.get_countries = AsyncMock(return_value=[{"id": 1, "name": "Spain"}, {"id": 2, "name": "France"}])
    service.get_artists = AsyncMock(return_value=[{"id": 10, "name": "Artist A"}])
    service.get_stamp_types = AsyncMock(return_value=[{"id": 20, "name": "Definitive"}])
    service.get_paper_types = AsyncMock(return_value=[{"id": 30, "name": "Paper X"}])
    service.get_print_types = AsyncMock(return_value=[{"id": 40, "name": "Lithography"}])
    service.get_printers = AsyncMock(return_value=[{"id": 50, "name": "Printer Y"}])
    service.get_years = AsyncMock(return_value=[{"id": 1, "year": 2020}, {"id": 2, "year": 2021}, {"id": 3, "year": 2022}])
    service.create_country = AsyncMock(return_value=None)
    service.create_artist = AsyncMock(return_value=None)
    service.create_stamp_type = AsyncMock(return_value=None)
    service.create_paper_type = AsyncMock(return_value=None)
    service.create_print_type = AsyncMock(return_value=None)
    service.create_printer = AsyncMock(return_value=None)
    service.create_year = AsyncMock(return_value=None)
    service.create_issue = AsyncMock(return_value=None)
    return service


sample_years_response: MagicMock = MagicMock(spec=requests.Response)
sample_years_response.status_code = 200
sample_years_response.json.return_value = {
    "data": [{"id": 1, "year": 2020}, {"id": 2, "year": 2021}, {"id": 3, "year": 2022}]
}


class TestIssueFormInit:
    """Tests for IssueForm initialization and basic structure."""

    def test_init_stores_references(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = IssueForm(page=mock_page, issue_service=mock_service, on_success=lambda: None)
        assert form.page is mock_page
        assert form._service is mock_service
        assert form._on_success is not None
        assert form._dlg is None


class TestIssueFormShow:
    """Tests for the show() method."""

    async def test_show_creates_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        form = IssueForm(page=mock_page, issue_service=mock_service)
        mock_service.get_years = AsyncMock(return_value=sample_years_response)

        await form.show()

        assert form._dlg is not None
        assert form._dlg in mock_page.overlay
        assert form._dlg.open is True

    async def test_show_fetches_reference_data(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        mock_service.get_countries.assert_awaited_once()
        mock_service.get_artists.assert_awaited_once()
        mock_service.get_stamp_types.assert_awaited_once()
        mock_service.get_paper_types.assert_awaited_once()
        mock_service.get_print_types.assert_awaited_once()
        mock_service.get_printers.assert_awaited_once()

    async def test_show_populates_reference_data(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert len(form._countries) == 2
        assert len(form._artists) == 1

    async def test_show_builds_form_fields(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert form._name_field is not None
        assert form._country_dropdown is not None
        assert form._description_field is not None
        assert form._notes_field is not None

    async def test_show_loads_initial_loading_view(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        content = form._dlg.content
        assert content is not None


class TestIssueFormCancel:
    """Tests for the cancel action."""

    async def test_cancel_closes_dialog(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._on_cancel(MagicMock())

        assert form._dlg.open is False


class TestIssueFormCreate:
    """Tests for the create/submit action."""

    async def test_create_without_name_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.name_required")

    async def test_create_with_invalid_mnh_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._name_field.value = "Test Series"
        form._mint_field.value = "invalid"

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.invalid_mnh")

    async def test_create_with_invalid_used_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._name_field.value = "Test Series"
        form._used_field.value = "invalid"

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.invalid_used")

    async def test_create_with_invalid_total_printed_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._name_field.value = "Test Series"
        form._total_printed_field.value = "invalid"

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.invalid_total_printed")

    async def test_create_with_existing_id_uses_directly(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 1
        mock_service.create_country.assert_not_called()

    async def test_create_with_typed_text_creates_new(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 1

    async def test_create_with_creation_failed_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 400
        resp.json.return_value = {}
        mock_service.create_issue = AsyncMock(return_value=resp)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_year_resolves_from_cache_first(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())
        await _set_minimal_fields(form)

        await form._on_create(MagicMock())

        mock_service.create_year.assert_not_called()
        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["year"] == 2

    async def test_create_year_creates_new_when_not_cached(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_year = AsyncMock(return_value=99)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        test_date = datetime.date(2023, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())
        await _set_minimal_fields(form)

        await form._on_create(MagicMock())

        mock_service.create_year.assert_awaited_once_with(2023)
        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["year"] == 99

    async def test_create_year_creation_failed_shows_error(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_year = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        test_date = datetime.date(2023, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())
        await _set_minimal_fields(form)

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_on_success_200(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        mock_service.create_issue = AsyncMock(return_value=resp)
        on_success = MagicMock()
        form = IssueForm(page=mock_page, issue_service=mock_service, on_success=on_success)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        on_success.assert_called_once()

    async def test_create_on_success_201(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 201
        mock_service.create_issue = AsyncMock(return_value=resp)
        on_success = MagicMock()
        form = IssueForm(page=mock_page, issue_service=mock_service, on_success=on_success)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        on_success.assert_called_once()

    async def test_create_builds_payload_with_all_fields(
        self, mock_page: MagicMock, mock_service: MagicMock
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._name_field.value = "Complete Series"
        form._country_dropdown._dropdown.value = "1"
        form._country_dropdown._selected_id = 1
        form._artist_dropdown._dropdown.value = "10"
        form._artist_dropdown._selected_id = 10
        form._stamp_type_dropdown._dropdown.value = "20"
        form._stamp_type_dropdown._selected_id = 20
        form._perforation_field.value = "Zebra 13"
        form._paper_type_dropdown._dropdown.value = "30"
        form._paper_type_dropdown._selected_id = 30
        form._printer_dropdown._dropdown.value = "50"
        form._printer_dropdown._selected_id = 50
        form._print_type_dropdown._dropdown.value = "40"
        form._print_type_dropdown._selected_id = 40
        form._mint_field.value = "1.50"
        form._used_field.value = "0.75"
        form._total_printed_field.value = "500000"
        form._description_field.value = "A test series"
        form._notes_field.value = "Some notes"
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["name"] == "Complete Series"
        assert payload["country"] == 1
        assert payload["artist"] == 10
        assert payload["stamp_type"] == 20
        assert payload["perforation"] == "Zebra 13"
        assert payload["paper_type"] == 30
        assert payload["printer"] == 50
        assert payload["print_type"] == 40
        assert payload["year"] == 2
        assert payload["market_value_mnh"] == 1.50
        assert payload["market_value_used"] == 0.75
        assert payload["total_printed"] == 500000
        assert payload["description"] == "A test series"
        assert payload["note"] == "Some notes"

    async def test_create_closes_dialog_on_success(
        self, mock_page: MagicMock, mock_service: MagicMock
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())
        dlg = form._dlg

        await form._on_create(MagicMock())

        assert dlg.open is False

    async def test_create_network_error_shows_snack_bar(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_api_error_shows_snack_bar(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        error_resp = MagicMock(spec=requests.Response)
        error_resp.status_code = 400
        error_resp.json.return_value = {"message": "Bad Request"}
        mock_service.create_issue = AsyncMock(return_value=error_resp)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == "Bad Request"


class TestIssueFormClose:
    """Tests for the close method."""

    async def test_close_cleans_up(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        dlg = form._dlg
        form.close()

        assert dlg.open is False


class TestIssueFormReferenceDataErrors:
    """Tests for graceful handling of reference data fetch failures."""

    async def test_all_reference_data_failures(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_countries = AsyncMock(return_value=[])
        mock_service.get_artists = AsyncMock(return_value=[])
        mock_service.get_stamp_types = AsyncMock(return_value=[])
        mock_service.get_paper_types = AsyncMock(return_value=[])
        mock_service.get_print_types = AsyncMock(return_value=[])
        mock_service.get_printers = AsyncMock(return_value=[])
        mock_service.get_years = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert form._countries == []
        assert form._artists == []
        assert form._name_field is not None


class TestIssueFormEditableDropdown:
    """Tests for editable dropdown behavior (int for IDs, str for custom text)."""

    async def test_create_with_custom_text_value(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_country = AsyncMock(return_value=99)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._name_field.value = "Custom Country Issue"
        form._artist_dropdown._dropdown.value = "10"
        form._artist_dropdown._selected_id = 10
        form._stamp_type_dropdown._dropdown.value = "20"
        form._stamp_type_dropdown._selected_id = 20
        form._paper_type_dropdown._dropdown.value = "30"
        form._paper_type_dropdown._selected_id = 30
        form._printer_dropdown._dropdown.value = "50"
        form._printer_dropdown._selected_id = 50
        form._print_type_dropdown._dropdown.value = "40"
        form._print_type_dropdown._selected_id = 40
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        with patch.object(type(form._country_dropdown), "text", new_callable=PropertyMock, return_value="My Custom Country"):
            await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        mock_service.create_country.assert_awaited_once_with("My Custom Country")
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 99

    async def test_create_with_id_value(self, mock_page: MagicMock, mock_service: MagicMock) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await _set_minimal_fields(form)
        test_date = datetime.date(2021, 6, 15)
        form._selected_date = test_date
        form._date_label.value = fmt_date(test_date.isoformat(), get_language())

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 1


async def _set_minimal_fields(form: IssueForm, name: str = "Test Series") -> None:
    """Set required name + all dropdown values to avoid None crash in _resolve_ref."""
    form._name_field.value = name
    form._country_dropdown._dropdown.value = "1"
    form._country_dropdown._selected_id = 1
    form._artist_dropdown._dropdown.value = "10"
    form._artist_dropdown._selected_id = 10
    form._stamp_type_dropdown._dropdown.value = "20"
    form._stamp_type_dropdown._selected_id = 20
    form._paper_type_dropdown._dropdown.value = "30"
    form._paper_type_dropdown._selected_id = 30
    form._printer_dropdown._dropdown.value = "50"
    form._printer_dropdown._selected_id = 50
    form._print_type_dropdown._dropdown.value = "40"
    form._print_type_dropdown._selected_id = 40
