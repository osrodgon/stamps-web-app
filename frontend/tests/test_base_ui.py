"""Unit tests for core/base_ui.py — background, user session, and notification helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.base_ui import BaseUI
from core.severity import Severity


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
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("test-token", {"user_id": 1, "username": "test"})

            mock_prefs.set.assert_any_call("token", "test-token")

    async def test_saves_user_id(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 42, "username": "test"})

            id_calls = [call for call in mock_prefs.set.call_args_list if "id" in str(call)]
            assert any("42" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_username(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "admin"})

            assert any("admin" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_is_admin(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "is_admin": True})

            assert any("True" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_first_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "first_name": "John"})

            assert any("John" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_last_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "last_name": "Doe"})

            assert any("Doe" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_email(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._save_user("token", {"user_id": 1, "username": "test", "email": "test@example.com"})

            assert any("test@example.com" in str(call) for call in mock_prefs.set.call_args_list)

    async def test_saves_all_fields(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.set = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
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
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            token_calls = [call for call in mock_prefs.remove.call_args_list if "token" in str(call)]
            assert len(token_calls) >= 1

    async def test_removes_user_id(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            id_calls = [call for call in mock_prefs.remove.call_args_list if "id" in str(call)]
            assert len(id_calls) >= 1

    async def test_removes_username(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            name_calls = [call for call in mock_prefs.remove.call_args_list if "name" in str(call)]
            assert len(name_calls) >= 1

    async def test_removes_all_fields(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            assert mock_prefs.remove.call_count == 7

    async def test_removes_email(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            email_calls = [call for call in mock_prefs.remove.call_args_list if "email" in str(call)]
            assert len(email_calls) >= 1

    async def test_removes_is_admin(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            admin_calls = [call for call in mock_prefs.remove.call_args_list if "admin" in str(call)]
            assert len(admin_calls) >= 1

    async def test_removes_first_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            first_calls = [call for call in mock_prefs.remove.call_args_list if "first" in str(call)]
            assert len(first_calls) >= 1

    async def test_removes_last_name(self, ui: BaseUI) -> None:
        mock_prefs = MagicMock()
        mock_prefs.remove = AsyncMock()
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            await ui._delete_user()

            last_calls = [call for call in mock_prefs.remove.call_args_list if "last" in str(call)]
            assert len(last_calls) >= 1
