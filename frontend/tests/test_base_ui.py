"""Unit tests for core/base_ui.py — background, user session, and notification helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.base_ui import BaseUI
from core.severity import Severity
from settings import (
    USER_JWT_TOKEN,
    USER_ID,
    USER_NAME,
    USER_IS_ADMIN,
    USER_FIRST_NAME,
    USER_LAST_NAME,
    USER_EMAIL,
)


class TestSetBackground:
    """Tests for the _set_background method."""

    @pytest.fixture
    def ui(self) -> BaseUI:
        return BaseUI()

    def test_returns_container_with_image_when_file_exists(self, ui: BaseUI) -> None:
        mock_container = MagicMock()
        with patch("os.path.exists", return_value=True), \
             patch("flet.Container", return_value=mock_container) as mock_ctr:
            result = ui._set_background("background.webp")

            assert result is mock_container
            assert mock_ctr.call_count == 2
            image_call = mock_ctr.call_args_list[1]
            call_kwargs = image_call[1]
            assert call_kwargs["expand"] is True
            assert "image" in call_kwargs

    def test_returns_container_with_color_when_file_missing(self, ui: BaseUI) -> None:
        mock_container = MagicMock()
        with patch("os.path.exists", return_value=False), \
             patch("flet.Container", return_value=mock_container) as mock_ctr:
            result = ui._set_background("missing.webp")

            assert result is mock_container
            assert mock_ctr.call_count == 1
            call_kwargs = mock_ctr.call_args[1]
            assert call_kwargs["expand"] is True
            assert "bgcolor" in call_kwargs
            assert "image" not in call_kwargs

    def test_image_container_has_no_bgcolor(self, ui: BaseUI) -> None:
        mock_container = MagicMock()
        with patch("os.path.exists", return_value=True), \
             patch("flet.Container", return_value=mock_container) as mock_ctr:
            ui._set_background("background.webp")

            image_call = mock_ctr.call_args_list[1]
            call_kwargs = image_call[1]
            assert "bgcolor" not in call_kwargs

    def test_fallback_container_has_bgcolor(self, ui: BaseUI) -> None:
        mock_container = MagicMock()
        with patch("os.path.exists", return_value=False), \
             patch("flet.Container", return_value=mock_container) as mock_ctr:
            ui._set_background("missing.webp")

            call_kwargs = mock_ctr.call_args[1]
            assert "bgcolor" in call_kwargs


class TestSaveUser:
    """Tests for the _save_user async method."""

    @pytest.fixture
    def ui(self) -> BaseUI:
        return BaseUI()

    async def test_saves_jwt_token(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("test-token", {"user_id": 1, "username": "test"})

            mock_prefs.set.assert_any_call(USER_JWT_TOKEN, "test-token")

    async def test_saves_user_id(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 42, "username": "test"})

            mock_prefs.set.assert_any_call(USER_ID, 42)

    async def test_saves_username(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "admin"})

            mock_prefs.set.assert_any_call(USER_NAME, "admin")

    async def test_saves_is_admin(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "is_admin": True})

            mock_prefs.set.assert_any_call(USER_IS_ADMIN, True)

    async def test_saves_first_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "first_name": "John"})

            mock_prefs.set.assert_any_call(USER_FIRST_NAME, "John")

    async def test_saves_last_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "last_name": "Doe"})

            mock_prefs.set.assert_any_call(USER_LAST_NAME, "Doe")

    async def test_saves_email(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "email": "test@example.com"})

            mock_prefs.set.assert_any_call(USER_EMAIL, "test@example.com")

    async def test_saves_all_fields(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            user_data = {
                "user_id": 1,
                "username": "testuser",
                "is_admin": False,
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
            }
            await ui._save_user("jwt-token-123", user_data)

            assert mock_prefs.set.call_count == 7


class TestDeleteUser:
    """Tests for the _delete_user async method."""

    @pytest.fixture
    def ui(self) -> BaseUI:
        return BaseUI()

    async def test_removes_jwt_token(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_JWT_TOKEN)

    async def test_removes_user_id(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_ID)

    async def test_removes_username(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_NAME)

    async def test_removes_all_fields(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            assert mock_prefs.remove.call_count == 7

    async def test_removes_email(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_EMAIL)

    async def test_removes_is_admin(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_IS_ADMIN)

    async def test_removes_first_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_FIRST_NAME)

    async def test_removes_last_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            mock_prefs.remove.assert_any_call(USER_LAST_NAME)
