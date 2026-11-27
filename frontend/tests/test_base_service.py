"""Unit tests for services/base_service.py — HTTP request layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from services.base_service import BaseService


class TestBaseServiceMakeRequest:
    """Tests for the _make_request method covering all HTTP methods and error handling."""

    @pytest.fixture
    def service(self) -> BaseService:
        return BaseService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_get_request(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            result = await service._make_request(BaseService.GET, "https://api.example.com/data")

            assert result is mock_response
            mock_thread.assert_called_once()
            call_args = mock_thread.call_args
            assert call_args[0][0] is requests.get
            assert call_args[0][1] == "https://api.example.com/data"

    async def test_post_request(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            payload = {"key": "value"}
            result = await service._make_request(BaseService.POST, "https://api.example.com/data", payload=payload)

            assert result is mock_response
            call_args = mock_thread.call_args
            assert call_args[0][0] is requests.post
            assert call_args[1]["json"] == payload

    async def test_put_request(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            payload = {"key": "updated"}
            headers = {"Authorization": "Bearer token"}
            result = await service._make_request(
                BaseService.PUT, "https://api.example.com/data/1", payload=payload, headers=headers
            )

            assert result is mock_response
            call_args = mock_thread.call_args
            assert call_args[0][0] is requests.put
            assert call_args[1]["headers"] == headers

    async def test_delete_request(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            result = await service._make_request(BaseService.DELETE, "https://api.example.com/data/1")

            assert result is mock_response
            call_args = mock_thread.call_args
            assert call_args[0][0] is requests.delete

    async def test_unknown_request_type_defaults_to_get(
        self, service: BaseService, mock_response: MagicMock
    ) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            result = await service._make_request(99, "https://api.example.com/data")

            assert result is mock_response
            call_args = mock_thread.call_args
            assert call_args[0][0] is requests.get

    async def test_network_error_returns_none(self, service: BaseService) -> None:
        with patch(
            "asyncio.to_thread", new_callable=AsyncMock, side_effect=requests.exceptions.RequestException("timeout")
        ):
            result = await service._make_request(BaseService.GET, "https://api.example.com/data")

            assert result is None

    async def test_connection_error_returns_none(self, service: BaseService) -> None:
        with patch(
            "asyncio.to_thread", new_callable=AsyncMock, side_effect=requests.exceptions.ConnectionError("refused")
        ):
            result = await service._make_request(BaseService.POST, "https://api.example.com/data")

            assert result is None

    async def test_request_with_headers(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            headers = {"Authorization": "Api-Key test123", "Content-Type": "application/json"}
            await service._make_request(BaseService.GET, "https://api.example.com/secure", headers=headers)

            call_args = mock_thread.call_args
            assert call_args[1]["headers"] == headers

    async def test_request_with_payload_and_headers(
        self, service: BaseService, mock_response: MagicMock
    ) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            payload = {"username": "test"}
            headers = {"Authorization": "Bearer token"}
            await service._make_request(BaseService.POST, "https://api.example.com/login", payload=payload, headers=headers)

            call_args = mock_thread.call_args
            assert call_args[1]["json"] == payload
            assert call_args[1]["headers"] == headers

    async def test_request_uses_timeout_180(self, service: BaseService, mock_response: MagicMock) -> None:
        with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_response) as mock_thread:
            await service._make_request(BaseService.GET, "https://api.example.com/data")

            call_args = mock_thread.call_args
            assert call_args[1]["timeout"] == 180


class TestBaseServiceConstants:
    """Tests for HTTP method constants."""

    def test_get_constant(self) -> None:
        assert BaseService.GET == 1

    def test_post_constant(self) -> None:
        assert BaseService.POST == 2

    def test_put_constant(self) -> None:
        assert BaseService.PUT == 3

    def test_delete_constant(self) -> None:
        assert BaseService.DELETE == 4
