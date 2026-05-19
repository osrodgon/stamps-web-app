"""Unit tests for services/issue_service.py — stamp issue API calls."""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest
import requests

from services.issue_service import IssueService


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
