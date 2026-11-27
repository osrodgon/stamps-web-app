"""Unit tests for services/issue_service.py — stamp issue API calls."""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest
import requests

from services.issue_service import IssueService
from core.urls import URLs
from settings import API_MASTER_KEY


class TestIssueServiceGetIssues:
    """Tests for the get_issues method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_get_issues_default_params(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            result = await service.get_issues()

            assert result is mock_response
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.GET
            expected_params = {"page": 1, "pageSize": 15, "sortBy": "date", "order": "asc"}
            from urllib.parse import parse_qs, urlparse
            assert parse_qs(urlparse(call_kwargs["url"]).query) == {k: [str(v)] for k, v in expected_params.items()}

    async def test_get_issues_with_custom_pagination(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(page=3, page_size=25)

            call_kwargs = mock_req.call_args[1]
            assert "page=3" in call_kwargs["url"]
            assert "pageSize=25" in call_kwargs["url"]

    async def test_get_issues_with_sort_params(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(sort_by="name", order="desc")

            call_kwargs = mock_req.call_args[1]
            assert "sortBy=name" in call_kwargs["url"]
            assert "order=desc" in call_kwargs["url"]

    async def test_get_issues_with_name_filter(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(name="Marianne")

            call_kwargs = mock_req.call_args[1]
            assert "name=Marianne" in call_kwargs["url"]

    async def test_get_issues_without_name_filter_omits_param(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(name="")

            call_kwargs = mock_req.call_args[1]
            from urllib.parse import parse_qs, urlparse
            assert "name" not in parse_qs(urlparse(call_kwargs["url"]).query)

    async def test_get_issues_with_year_filter(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(year="2020")

            call_kwargs = mock_req.call_args[1]
            assert "year=2020" in call_kwargs["url"]

    async def test_get_issues_with_year_range_filter(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.get_issues(year="2000-2010")

            call_kwargs = mock_req.call_args[1]
            assert "year=2000-2010" in call_kwargs["url"]

    async def test_get_issues_includes_api_key_header(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from settings import API_MASTER_KEY

            await service.get_issues()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_get_issues_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_issues()

            assert result is None


class TestIssueServiceDeleteIssue:
    """Tests for the delete_issue method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 204
        return response

    async def test_delete_issue_correct_url(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            result = await service.delete_issue(42)

            assert result is mock_response
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.DELETE
            assert "42/" in call_kwargs["url"]

    async def test_delete_issue_includes_api_key_header(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from settings import API_MASTER_KEY

            await service.delete_issue(1)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_delete_issue_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.delete_issue(99)

            assert result is None


class TestIssueServiceGetIssueStamps:
    """Tests for the get_issue_stamps method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_get_issue_stamps_correct_url(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            result = await service.get_issue_stamps(7)

            assert result is mock_response
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.GET
            assert "issue_id=7" in call_kwargs["url"]

    async def test_get_issue_stamps_includes_api_key_header(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from settings import API_MASTER_KEY

            await service.get_issue_stamps(1)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_get_issue_stamps_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_issue_stamps(1)

            assert result is None


class TestIssueServiceUpdateStamp:
    """Tests for the update_stamp method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_update_stamp_correct_url(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            result = await service.update_stamp(7, {"name": "Updated"})

            assert result is mock_response
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.PUT
            assert call_kwargs["url"] == f"{URLs.Backend.stamps}7"

    async def test_update_stamp_sends_payload(self, service: IssueService, mock_response: MagicMock) -> None:
        payload: dict = {"name": "Updated", "face_value": "3.00"}
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.update_stamp(7, payload)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["payload"] == payload

    async def test_update_stamp_includes_auth_header(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.update_stamp(1, {})

            call_kwargs = mock_req.call_args[1]
            from settings import API_MASTER_KEY
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_update_stamp_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.update_stamp(1, {})
            assert result is None


class TestIssueServiceGetYears:
    """Tests for the get_years method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_get_years_correct_endpoint(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from core.urls import URLs

            result = await service.get_years()

            assert result is mock_response
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.years
            assert call_kwargs["request_type"] == service.GET

    async def test_get_years_includes_api_key_header(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from settings import API_MASTER_KEY

            await service.get_years()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_get_years_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_years()

            assert result is None


class TestIssueServiceCreateIssue:
    """Tests for the create_issue method."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        return response

    async def test_create_issue_sends_post(self, service: IssueService, mock_response: MagicMock) -> None:
        payload: dict = {"name": "Test Series", "year": 1}
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            result = await service.create_issue(payload)

            assert result is mock_response
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["payload"] == payload

    async def test_create_issue_correct_endpoint(self, service: IssueService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from core.urls import URLs

            await service.create_issue({"name": "Test"})

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.issues

    async def test_create_issue_includes_api_key_header(
        self, service: IssueService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.create_issue({"name": "Test"})

            call_kwargs = mock_req.call_args[1]
            assert "Authorization" in call_kwargs["headers"]

    async def test_create_issue_returns_none_on_error(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.create_issue({"name": "Test"})

            assert result is None


class TestIssueServiceReferenceData:
    """Tests for reference data fetch methods (get_countries, get_artists, etc.)."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_ok_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        response.json.return_value = {
            "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        }
        return response

    @pytest.fixture
    def mock_error_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 500
        return response

    async def test_get_countries_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_countries()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_countries_error_returns_empty(
        self, service: IssueService, mock_error_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_countries()

            assert result == []

    async def test_get_countries_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_countries()

            assert result == []

    async def test_get_countries_correct_endpoint(self, service: IssueService, mock_ok_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_countries()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.countries
            assert call_kwargs["request_type"] == service.GET

    async def test_get_artists_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_artists()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_artists_error_returns_empty(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_artists()

            assert result == []

    async def test_get_artists_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_artists()

            assert result == []

    async def test_get_artists_correct_endpoint(self, service: IssueService, mock_ok_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_artists()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.artists
            assert call_kwargs["request_type"] == service.GET

    async def test_get_stamp_types_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_stamp_types()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_stamp_types_error_returns_empty(
        self, service: IssueService, mock_error_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_stamp_types()

            assert result == []

    async def test_get_stamp_types_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_stamp_types()

            assert result == []

    async def test_get_stamp_types_correct_endpoint(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_stamp_types()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.stamp_types
            assert call_kwargs["request_type"] == service.GET

    async def test_get_paper_types_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_paper_types()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_paper_types_error_returns_empty(
        self, service: IssueService, mock_error_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_paper_types()

            assert result == []

    async def test_get_paper_types_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_paper_types()

            assert result == []

    async def test_get_paper_types_correct_endpoint(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_paper_types()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.paper_types
            assert call_kwargs["request_type"] == service.GET

    async def test_get_print_types_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_print_types()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_print_types_error_returns_empty(
        self, service: IssueService, mock_error_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_print_types()

            assert result == []

    async def test_get_print_types_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_print_types()

            assert result == []

    async def test_get_print_types_correct_endpoint(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_print_types()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.print_types
            assert call_kwargs["request_type"] == service.GET

    async def test_get_printers_returns_list(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response):
            result = await service.get_printers()

            assert result == [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    async def test_get_printers_error_returns_empty(
        self, service: IssueService, mock_error_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.get_printers()

            assert result == []

    async def test_get_printers_network_error_returns_empty(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.get_printers()

            assert result == []

    async def test_get_printers_correct_endpoint(
        self, service: IssueService, mock_ok_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_ok_response) as mock_req:
            from core.urls import URLs

            await service.get_printers()

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["url"] == URLs.Backend.printers
            assert call_kwargs["request_type"] == service.GET


class TestIssueServiceCreateMethods:
    """Tests for the new create methods (country, artist, stamp_type, paper_type, print_type, printer, year)."""

    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

    @pytest.fixture
    def mock_created_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        response.json.return_value = {"data": {"id": 42, "name": "Test"}}
        return response

    @pytest.fixture
    def mock_error_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 400
        return response

    async def test_create_country_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_country("France")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.countries
            assert call_kwargs["payload"] == {"name": "France"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_country_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_country("France")
            assert result is None

    async def test_create_country_network_error_returns_none(self, service: IssueService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.create_country("France")
            assert result is None

    async def test_create_artist_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_artist("Picasso")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.artists
            assert call_kwargs["payload"] == {"name": "Picasso"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_artist_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_artist("Picasso")
            assert result is None

    async def test_create_stamp_type_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_stamp_type("Definitive")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.stamp_types
            assert call_kwargs["payload"] == {"name": "Definitive"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_stamp_type_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_stamp_type("Definitive")
            assert result is None

    async def test_create_paper_type_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_paper_type("Chalky")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.paper_types
            assert call_kwargs["payload"] == {"name": "Chalky"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_paper_type_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_paper_type("Chalky")
            assert result is None

    async def test_create_print_type_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_print_type("Lithography")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.print_types
            assert call_kwargs["payload"] == {"name": "Lithography"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_print_type_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_print_type("Lithography")
            assert result is None

    async def test_create_printer_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_printer("Security Printer")

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.printers
            assert call_kwargs["payload"] == {"name": "Security Printer"}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_printer_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_printer("Security Printer")
            assert result is None

    async def test_create_year_success(self, service: IssueService, mock_created_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_created_response) as mock_req:
            result = await service.create_year(2023)

            assert result == 42
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["url"] == URLs.Backend.years
            assert call_kwargs["payload"] == {"year": 2023}
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_create_year_returns_none_on_error(self, service: IssueService, mock_error_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_error_response):
            result = await service.create_year(2023)
            assert result is None
