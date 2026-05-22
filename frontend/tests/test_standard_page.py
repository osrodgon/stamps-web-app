"""Unit tests for components/templates/standard_page.py — base page template."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import flet as ft

from components.templates.standard_page import StandardPage


class TestStandardPageInit:
    """Tests for StandardPage construction."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        return MagicMock(route="/test")

    def test_stores_main_page(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            sp = StandardPage(page=page_mock)

        assert sp.main_page is page_mock

    def test_header_created_with_height(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            sp = StandardPage(page=page_mock)

        assert isinstance(sp.header, ft.Container)
        assert sp.header.height == 80
        assert sp.header.expand is False

    def test_main_created_with_expand(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            sp = StandardPage(page=page_mock)

        assert isinstance(sp.main, ft.Container)
        assert sp.main.expand is True

    def test_custom_header_height(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            sp = StandardPage(page=page_mock, header_height=100)

        assert sp.header.height == 100


class TestStandardPageSetAppHeader:
    """Tests for set_app_header."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        return MagicMock(route="/test")

    @pytest.fixture
    def sp(self, page_mock: MagicMock) -> StandardPage:
        with patch.object(ft.View, "__init__", return_value=None):
            return StandardPage(page=page_mock)

    def test_sets_header_content(self, sp: StandardPage) -> None:
        app_header = MagicMock(spec=ft.Container)
        result = sp.set_app_header(app_header)
        assert sp.header.content is app_header
        assert result is app_header

    def test_returns_app_header(self, sp: StandardPage) -> None:
        app_header = MagicMock(spec=ft.Container)
        result = sp.set_app_header(app_header)
        assert result is app_header


class TestStandardPageLogMethods:
    """Tests for request_settings, request_profile, logout."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        return MagicMock(route="/test")

    @pytest.fixture
    def sp(self, page_mock: MagicMock) -> StandardPage:
        with patch.object(ft.View, "__init__", return_value=None):
            sp = StandardPage(page=page_mock)
            sp._log = MagicMock()
            return sp

    def test_request_settings_logs(self, sp: StandardPage) -> None:
        sp.request_settings()
        sp._log.debug.assert_called_once()

    def test_request_profile_logs(self, sp: StandardPage) -> None:
        sp.request_profile()
        sp._log.debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_pushes_logout_route(self, sp: StandardPage) -> None:
        sp.main_page = AsyncMock()
        await sp.logout()
        sp.main_page.push_route.assert_called_once_with("/logout")

    @pytest.mark.asyncio
    async def test_logout_logs(self, sp: StandardPage) -> None:
        sp.main_page = AsyncMock()
        sp._log = MagicMock()
        await sp.logout()
        sp._log.debug.assert_called_once()
