"""Unit tests for main.py — entry point, routing, and page configuration."""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from main import configure_page, route_change, view_pop, ROUTE_HANDLERS
from core.urls import URLs


class TestROUTE_HANDLERS:
    """Tests for the ROUTE_HANDLERS dictionary."""

    def test_is_dict(self) -> None:
        assert isinstance(ROUTE_HANDLERS, dict)

    def test_has_login_key(self) -> None:
        assert URLs.Frontend.login in ROUTE_HANDLERS

    def test_has_signup_key(self) -> None:
        assert URLs.Frontend.signup in ROUTE_HANDLERS

    def test_has_collections_key(self) -> None:
        assert URLs.Frontend.collections in ROUTE_HANDLERS

    def test_has_stamps_manager_key(self) -> None:
        assert URLs.Frontend.stamps_manager in ROUTE_HANDLERS

    def test_logout_not_mapped(self) -> None:
        assert URLs.Frontend.logout not in ROUTE_HANDLERS


class TestConfigurePage:
    """Tests for configure_page function."""

    def test_sets_title(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert page.title is not None

    def test_sets_expand_true(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert page.expand is True

    def test_sets_fonts(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert page.fonts is not None

    def test_sets_theme(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert page.theme is not None

    def test_sets_window_icon(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert page.window.icon is not None

    def test_fonts_contain_roboto_keys(self) -> None:
        page = MagicMock()
        configure_page(page)
        assert "Roboto" in page.fonts
        assert "Roboto-Bold" in page.fonts
        assert "Roboto-Black" in page.fonts


class TestRouteChange:
    """Tests for the route_change async handler."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        page = MagicMock()
        page.push_route = AsyncMock()
        page.route = URLs.Frontend.login
        page.views = []
        return page

    @pytest.fixture
    def event_mock(self, page_mock: MagicMock) -> MagicMock:
        event = MagicMock()
        event.page = page_mock
        return event

    @pytest.mark.asyncio
    async def test_root_route_no_auth_redirects_to_login(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.root
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            prefs_instance = MagicMock()
            prefs_instance.get = AsyncMock(return_value=None)
            mock_prefs.return_value = prefs_instance

            await route_change(event_mock)

        event_mock.page.push_route.assert_called_once_with(URLs.Frontend.login)

    @pytest.mark.asyncio
    async def test_root_route_admin_redirects_to_stamps(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.root
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            prefs_instance = MagicMock()
            prefs_instance.get = AsyncMock(side_effect=["token123", True])
            mock_prefs.return_value = prefs_instance

            await route_change(event_mock)

        event_mock.page.push_route.assert_called_once_with(URLs.Frontend.stamps_manager)

    @pytest.mark.asyncio
    async def test_root_route_user_redirects_to_collections(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.root
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            prefs_instance = MagicMock()
            prefs_instance.get = AsyncMock(side_effect=["token123", False])
            mock_prefs.return_value = prefs_instance

            await route_change(event_mock)

        event_mock.page.push_route.assert_called_once_with(URLs.Frontend.collections)

    @pytest.mark.asyncio
    async def test_known_route_appends_handler(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.login
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            mock_prefs.return_value = MagicMock()
            mock_prefs.return_value.get = AsyncMock(return_value=None)

            await route_change(event_mock)

        assert len(event_mock.page.views) == 1

    @pytest.mark.asyncio
    async def test_logout_route_deletes_user_and_redirects(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.logout
        with patch.object(ft, "SharedPreferences") as mock_prefs, \
             patch("main.BaseUI") as mock_base:
            mock_prefs.return_value = MagicMock()
            base_instance = MagicMock()
            base_instance._delete_user = AsyncMock()
            mock_base.return_value = base_instance

            await route_change(event_mock)

        base_instance._delete_user.assert_called_once()
        event_mock.page.push_route.assert_called_once_with(URLs.Frontend.login)

    @pytest.mark.asyncio
    async def test_unknown_route_shows_not_found(self, event_mock: MagicMock) -> None:
        event_mock.page.route = "/nonexistent"
        with patch.object(ft, "SharedPreferences") as mock_prefs, \
             patch("main.NotFoundPage") as mock_not_found:
            mock_prefs.return_value = MagicMock()
            mock_prefs.return_value.get = AsyncMock(return_value=None)
            mock_not_found.return_value = MagicMock()

            await route_change(event_mock)

            mock_not_found.assert_called_once_with(event_mock.page)
            assert len(event_mock.page.views) == 1

    @pytest.mark.asyncio
    async def test_known_route_clears_views(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.login
        event_mock.page.views = [MagicMock(), MagicMock()]
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            mock_prefs.return_value = MagicMock()
            mock_prefs.return_value.get = AsyncMock(return_value=None)

            await route_change(event_mock)

        assert len(event_mock.page.views) == 1

    @pytest.mark.asyncio
    async def test_calls_page_update(self, event_mock: MagicMock) -> None:
        event_mock.page.route = URLs.Frontend.login
        with patch.object(ft, "SharedPreferences") as mock_prefs:
            mock_prefs.return_value = MagicMock()
            mock_prefs.return_value.get = AsyncMock(return_value=None)

            await route_change(event_mock)

        event_mock.page.update.assert_called_once()


class TestViewPop:
    """Tests for the view_pop handler."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        page = MagicMock()
        page.push_route = AsyncMock()
        return page

    @pytest.fixture
    def event_mock(self, page_mock: MagicMock) -> MagicMock:
        event = MagicMock()
        event.page = page_mock
        return event

    @pytest.mark.asyncio
    async def test_removes_view(self, event_mock: MagicMock) -> None:
        view = MagicMock(route="/previous")
        event_mock.view = view
        event_mock.page.views = [MagicMock(route="/first"), view]

        await view_pop(event_mock)

        assert len(event_mock.page.views) == 1

    @pytest.mark.asyncio
    async def test_pushes_top_view_route(self, event_mock: MagicMock) -> None:
        view = MagicMock(route="/previous")
        top_view = MagicMock(route="/current")
        event_mock.view = view
        event_mock.page.views = [MagicMock(route="/first"), top_view, view]

        await view_pop(event_mock)

        event_mock.page.push_route.assert_called_once_with("/current")

    @pytest.mark.asyncio
    async def test_noop_when_no_view(self, event_mock: MagicMock) -> None:
        event_mock.view = None
        event_mock.page.views = [MagicMock(route="/first")]

        await view_pop(event_mock)

        event_mock.page.push_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_when_no_views_left_after_remove(self, event_mock: MagicMock) -> None:
        view = MagicMock(route="/only")
        event_mock.view = view
        event_mock.page.views = [view]

        await view_pop(event_mock)

        assert len(event_mock.page.views) == 0
        event_mock.page.push_route.assert_not_called()
