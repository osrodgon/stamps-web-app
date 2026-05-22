"""Unit tests for pages/not_found_page.py — 404 Not Found page."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import flet as ft

from pages.not_found_page import NotFoundPage
from core.urls import URLs


class TestNotFoundPageInit:
    """Tests for NotFoundPage construction."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        return MagicMock(route="/nonexistent")

    def test_sets_route(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        assert page.route == URLs.Frontend.not_found

    def test_sets_padding(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        assert page.padding == 20

    def test_stores_main_page(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        assert page.main_page is page_mock

    def test_content_has_controls(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        assert len(page.controls) > 0

    def test_first_control_is_column(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        col = page.controls[0]
        assert isinstance(col, ft.Column)


@pytest.mark.asyncio
class TestNotFoundPageGoHome:
    """Tests for the _go_home navigation handler."""

    @pytest.fixture
    def page_mock(self) -> MagicMock:
        page = MagicMock(route="/nonexistent")
        page.push_route = AsyncMock()
        return page

    async def test_go_home_pushes_root_route(self, page_mock: MagicMock) -> None:
        with patch.object(ft.View, "__init__", return_value=None):
            page = NotFoundPage(page=page_mock)

        with patch.object(asyncio, "create_task", asyncio.ensure_future):
            page._go_home(None)
        await asyncio.sleep(0)

        page_mock.push_route.assert_called_once_with(URLs.Frontend.root)
