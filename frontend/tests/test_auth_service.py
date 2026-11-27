"""Unit tests for services/auth_service.py — authentication API calls."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from services.auth_service import AuthService


class TestAuthServiceLogin:
    """Tests for the login method."""

    @pytest.fixture
    def service(self) -> AuthService:
        return AuthService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        return response

    async def test_login_calls_correct_endpoint(
        self, service: AuthService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            payload = {"username": "testuser", "password": "testpass"}
            result = await service.login(payload)

            assert result is mock_response
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["payload"] == payload

    async def test_login_uses_post_method(self, service: AuthService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.login({"username": "user", "password": "pass"})

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST

    async def test_login_passes_payload(self, service: AuthService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            payload = {"username": "admin", "password": "secret123!"}
            await service.login(payload)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["payload"] == payload

    async def test_login_returns_none_on_error(self, service: AuthService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.login({"username": "bad", "password": "wrong"})

            assert result is None


class TestAuthServiceSignup:
    """Tests for the signup method."""

    @pytest.fixture
    def service(self) -> AuthService:
        return AuthService()

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = 201
        return response

    async def test_signup_calls_correct_endpoint(
        self, service: AuthService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            payload = {"username": "newuser", "email": "new@example.com", "password": "SecurePass1!"}
            result = await service.signup(payload)

            assert result is mock_response
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST
            assert call_kwargs["payload"] == payload

    async def test_signup_uses_post_method(self, service: AuthService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await service.signup({"username": "user", "email": "u@e.com", "password": "Pass1!"})

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["request_type"] == service.POST

    async def test_signup_includes_api_key_header(
        self, service: AuthService, mock_response: MagicMock
    ) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            from settings import API_MASTER_KEY

            await service.signup({"username": "user", "email": "u@e.com", "password": "Pass1!"})

            call_kwargs = mock_req.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == f"Api-Key {API_MASTER_KEY}"

    async def test_signup_passes_payload(self, service: AuthService, mock_response: MagicMock) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            payload = {"username": "test", "email": "test@example.com", "password": "Test1234!"}
            await service.signup(payload)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["payload"] == payload

    async def test_signup_returns_none_on_error(self, service: AuthService) -> None:
        with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=None):
            result = await service.signup({"username": "fail", "email": "f@e.com", "password": "Fail1234!"})

            assert result is None
