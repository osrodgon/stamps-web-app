"""Unit tests for components/issue_form/issue_form.py — Add Issue dialog."""

from unittest.mock import AsyncMock, MagicMock, patch

import datetime
import pytest
import flet as ft
import requests

from components.issue_form.issue_form import IssueForm
from core.translations import _


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock(spec=ft.Page)
    page.overlay = []
    page.show_dialog = MagicMock()
    return page


@pytest.fixture
def mock_service() -> MagicMock:
    service = MagicMock()
    service.get_years = AsyncMock(return_value=None)
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


@pytest.fixture(autouse=True)
def mock_shared_components() -> tuple[MagicMock, MagicMock]:
    with (
        patch("components.issue_form.issue_form.IssueHeaderSection") as mock_header_cls,
        patch("components.issue_form.issue_form.IssueSpecsGrid") as mock_specs_cls,
    ):
        mock_header = MagicMock()
        mock_header.name_text = ""
        mock_header.mint_value = 0.0
        mock_header.used_value = 0.0
        mock_header.total_printed_value = 0
        mock_header.date_value = datetime.date.today().isoformat()

        mock_specs = MagicMock()
        mock_specs.description_value = ""
        mock_specs.notes_value = ""
        mock_specs.edit_state = {}
        mock_specs.enter_edit_mode = AsyncMock(return_value=True)

        mock_header_cls.return_value = mock_header
        mock_specs_cls.return_value = mock_specs

        yield mock_header, mock_specs


def _set_minimal_fields(
    form: IssueForm,
    name: str = "Test Series",
    date_iso: str = "2021-06-15",
) -> None:
    form._header_section.name_text = name
    form._header_section.date_value = date_iso
    form._specs_grid.edit_state = {
        "country": {"ac": MagicMock(selected_id=1), "issue_key": "country", "create": MagicMock()},
        "artist": {"ac": MagicMock(selected_id=10), "issue_key": "artist", "create": MagicMock()},
        "stamp_type": {"ac": MagicMock(selected_id=20), "issue_key": "stamp_type", "create": MagicMock()},
        "paper_type": {"ac": MagicMock(selected_id=30), "issue_key": "paper_type", "create": MagicMock()},
        "printer": {"ac": MagicMock(selected_id=50), "issue_key": "printer", "create": MagicMock()},
        "print_type": {"ac": MagicMock(selected_id=40), "issue_key": "print_type", "create": MagicMock()},
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

    async def test_show_creates_dialog(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert form._dlg is not None
        assert form._dlg in mock_page.overlay
        assert form._dlg.open is True

    async def test_show_fetches_years(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        mock_service.get_years.assert_awaited_once()

    async def test_show_enters_edit_mode(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_header, mock_specs = mock_shared_components
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        mock_specs.enter_edit_mode.assert_awaited_once_with(mock_service)
        mock_header.enter_edit_mode.assert_called_once()

    async def test_show_builds_content(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        content = form._dlg.content
        assert content is not None
        controls = content.controls
        assert len(controls) == 2  # header+specs container + actions row

    async def test_show_stores_years(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert len(form._years) == 3

    async def test_show_handles_enter_edit_mode_failure(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_header, mock_specs = mock_shared_components
        mock_specs.enter_edit_mode = AsyncMock(return_value=False)
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert form._dlg.open is False


class TestIssueFormCancel:
    """Tests for the cancel action."""

    async def test_cancel_closes_dialog(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._on_cancel(MagicMock())

        assert form._dlg.open is False


class TestIssueFormCreate:
    """Tests for the create/submit action."""

    async def test_create_without_name_shows_error(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.name_required")

    async def test_create_with_existing_id_uses_directly(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 1, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 1
        mock_service.create_country.assert_not_called()

    async def test_create_with_typed_text_creates_new(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["country"] == 1

    async def test_create_with_creation_failed_shows_error(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 400
        resp.json.return_value = {}
        mock_service.create_issue = AsyncMock(return_value=resp)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_year_resolves_from_cache_first(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_year.assert_not_called()
        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["year"] == 2

    async def test_create_year_creates_new_when_not_cached(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_year = AsyncMock(return_value=99)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2023-06-15")
        form._years = [{"id": 1, "year": 2020}, {"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_year.assert_awaited_once_with(2023)
        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["year"] == 99

    async def test_create_year_creation_failed_shows_error(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_year = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2023-06-15")
        form._years = [{"id": 1, "year": 2020}, {"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_on_success_200(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        mock_service.create_issue = AsyncMock(return_value=resp)
        on_success = MagicMock()
        form = IssueForm(page=mock_page, issue_service=mock_service, on_success=on_success)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 1, "year": 2021}]

        await form._on_create(MagicMock())

        on_success.assert_called_once()

    async def test_create_on_success_201(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 201
        mock_service.create_issue = AsyncMock(return_value=resp)
        on_success = MagicMock()
        form = IssueForm(page=mock_page, issue_service=mock_service, on_success=on_success)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        on_success.assert_called_once()

    async def test_create_builds_payload_with_all_fields(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        form._header_section.name_text = "Complete Series"
        form._header_section.mint_value = 1.50
        form._header_section.used_value = 0.75
        form._header_section.total_printed_value = 500000
        form._header_section.date_value = "2021-06-15"
        form._specs_grid.description_value = "A test series"
        form._specs_grid.notes_value = "Some notes"
        form._specs_grid.edit_state = {
            "country": {"ac": MagicMock(selected_id=1), "issue_key": "country", "create": MagicMock()},
            "artist": {"ac": MagicMock(selected_id=10), "issue_key": "artist", "create": MagicMock()},
            "stamp_type": {"ac": MagicMock(selected_id=20), "issue_key": "stamp_type", "create": MagicMock()},
            "paper_type": {"ac": MagicMock(selected_id=30), "issue_key": "paper_type", "create": MagicMock()},
            "printer": {"ac": MagicMock(selected_id=50), "issue_key": "printer", "create": MagicMock()},
            "print_type": {"ac": MagicMock(selected_id=40), "issue_key": "print_type", "create": MagicMock()},
        }
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_awaited_once()
        payload = mock_service.create_issue.call_args[0][0]
        assert payload["name"] == "Complete Series"
        assert payload["country"] == 1
        assert payload["artist"] == 10
        assert payload["stamp_type"] == 20
        assert payload["paper_type"] == 30
        assert payload["printer"] == 50
        assert payload["print_type"] == 40
        assert payload["year"] == 2
        assert payload["market_value_mnh"] == "1.5"
        assert payload["market_value_used"] == "0.75"
        assert payload["total_printed"] == "500000"
        assert payload["description"] == "A test series"
        assert payload["note"] == "Some notes"

    async def test_create_closes_dialog_on_success(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(
            return_value=MagicMock(spec=requests.Response, status_code=201)
        )
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]
        dlg = form._dlg

        await form._on_create(MagicMock())

        assert dlg.open is False

    async def test_create_network_error_shows_snack_bar(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        mock_service.create_issue = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")

    async def test_create_api_error_shows_snack_bar(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        error_resp = MagicMock(spec=requests.Response)
        error_resp.status_code = 400
        error_resp.json.return_value = {"message": "Bad Request"}
        mock_service.create_issue = AsyncMock(return_value=error_resp)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        _set_minimal_fields(form, date_iso="2021-06-15")
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == "Bad Request"

    async def test_create_reference_creation_failure(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        # Set up edit_state with an AC that has no selected_id and non-empty text
        ac_no_id = MagicMock()
        ac_no_id.selected_id = None
        ac_no_id.text = "New Country"
        form._header_section.name_text = "Test"
        form._header_section.date_value = "2021-06-15"
        form._specs_grid.edit_state = {
            "country": {
                "ac": ac_no_id,
                "issue_key": "country",
                "create": AsyncMock(return_value=None),
            },
        }
        form._years = [{"id": 2, "year": 2021}]

        await form._on_create(MagicMock())

        mock_service.create_issue.assert_not_called()
        mock_page.show_dialog.assert_called_once()
        args = mock_page.show_dialog.call_args[0][0]
        assert isinstance(args, ft.SnackBar)
        assert args.content.value == _("issues.creation_failed")


class TestIssueFormClose:
    """Tests for the close method."""

    async def test_close_cleans_up(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=sample_years_response)
        form = IssueForm(page=mock_page, issue_service=mock_service)
        await form.show()

        dlg = form._dlg
        form.close()

        assert dlg.open is False


class TestIssueFormEmptyYears:
    """Tests for graceful handling when years endpoint returns nothing."""

    async def test_show_with_no_years(
        self, mock_page: MagicMock, mock_service: MagicMock, mock_shared_components: tuple[MagicMock, MagicMock]
    ) -> None:
        mock_service.get_years = AsyncMock(return_value=None)
        form = IssueForm(page=mock_page, issue_service=mock_service)

        await form.show()

        assert form._years == []
