"""Tests for the parameterised routes (plan step B3)."""

from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from core.routing import RouteResolver
from pages.collection.collection_issue_page import CollectionIssuePage
from pages.collection.collection_series_page import CollectionSeriesPage


class TestRouteResolver:
    """The exact table keeps its routes; this class adds the ones with ids."""

    @pytest.fixture
    def page(self) -> MagicMock:
        page = MagicMock(spec=ft.Page)
        page.route = "/collections/7"
        page.overlay = []
        page.run_task = MagicMock()
        page.update = MagicMock()
        page.push_route = AsyncMock()
        return page

    def test_the_series_route_builds_the_page(self, page):
        view = RouteResolver.view("/collections/7", page)

        assert isinstance(view, CollectionSeriesPage)
        assert view._collection_id == 7

    def test_the_exact_route_is_left_to_the_table(self, page):
        assert RouteResolver.view("/collections", page) is None

    def test_a_non_numeric_id_is_not_a_route(self, page):
        assert RouteResolver.view("/collections/abc", page) is None

    def test_the_series_detail_builds_the_page(self, page):
        view = RouteResolver.view("/collections/7/issues/3", page)

        assert isinstance(view, CollectionIssuePage)
        assert view._collection_id == 7
        assert view._issue_id == 3

    def test_an_unknown_route_is_not_resolved(self, page):
        assert RouteResolver.view("/somewhere", page) is None
