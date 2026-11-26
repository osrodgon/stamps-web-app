"""Tests for `MockLogin`, the development auto-login (2026-11-26).

The backend and the preferences are mocked: what matters is that the flag gates the
whole thing, that the credentials come from the environment and that the route
follows the user type.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import requests

from core.mock_login import MockLogin
from core.urls import URLs


class Answers:
    """A login response with that body and status."""

    @staticmethod
    def of(payload: dict, status: int = 200) -> MagicMock:
        """Build the response the service would return."""
        response = MagicMock(spec=requests.Response)
        response.status_code = status
        response.json.return_value = {"data": payload}
        return response


class LoginTest:
    """A configured mock login with its dependencies mocked."""

    @pytest.fixture(autouse=True)
    def configuration(self, mocker):
        """Turn the mock login on with known credentials."""
        mocker.patch("core.mock_login.MOCK_LOGIN", True)
        mocker.patch("core.mock_login.MOCK_USER", "test_user")
        mocker.patch("core.mock_login.MOCK_PASSWORD", "secret")

    @pytest.fixture
    def service(self) -> MagicMock:
        service = MagicMock()
        service.login = AsyncMock()
        return service

    @pytest.fixture
    def saved(self, mocker) -> AsyncMock:
        return mocker.patch.object(
            MockLogin, "_save_user", new_callable=AsyncMock
        )

    @staticmethod
    def session(is_admin: bool = False) -> dict:
        return {"token": "jwt", "payload": {"is_admin": is_admin}}


class TestItStaysOff(LoginTest):
    """The flag is the gate, and it is off by default."""

    async def test_a_disabled_flag_does_nothing(self, service, saved, mocker):
        mocker.patch("core.mock_login.MOCK_LOGIN", False)

        assert await MockLogin(service).run() is None
        service.login.assert_not_awaited()
        saved.assert_not_awaited()

    async def test_missing_credentials_do_nothing(self, service, saved, mocker):
        mocker.patch("core.mock_login.MOCK_USER", "")

        assert await MockLogin(service).run() is None
        service.login.assert_not_awaited()


class TestItLogsIn(LoginTest):
    """With the flag on, the session is stored and a route comes back."""

    async def test_a_normal_user_goes_to_collections(self, service, saved):
        service.login.return_value = Answers.of(self.session(is_admin=False))

        route = await MockLogin(service).run()

        assert route == URLs.Frontend.collections
        saved.assert_awaited_once_with("jwt", {"is_admin": False})

    async def test_an_admin_goes_to_the_manager(self, service, saved):
        service.login.return_value = Answers.of(self.session(is_admin=True))

        route = await MockLogin(service).run()

        assert route == URLs.Frontend.stamps_manager

    async def test_it_sends_the_credentials_from_the_environment(self, service, saved):
        service.login.return_value = Answers.of(self.session())

        await MockLogin(service).run()

        service.login.assert_awaited_once_with(
            {"username": "test_user", "password": "secret"}
        )


class TestItRefuses(LoginTest):
    """A refused or empty answer is no session, and nothing is stored."""

    async def test_a_rejected_login_returns_none(self, service, saved):
        service.login.return_value = Answers.of({"detail": "nope"}, status=401)

        assert await MockLogin(service).run() is None
        saved.assert_not_awaited()

    async def test_a_network_error_returns_none(self, service, saved):
        service.login.return_value = None

        assert await MockLogin(service).run() is None
        saved.assert_not_awaited()

    async def test_an_answer_without_a_session_returns_none(self, service, saved):
        service.login.return_value = Answers.of({"token": None, "payload": None})

        assert await MockLogin(service).run() is None
        saved.assert_not_awaited()
