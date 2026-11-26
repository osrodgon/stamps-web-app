"""Tests for the collections overview page (plan step A5).

`ft.View` cannot be built in this suite (the `_values` descriptor problem already
documented), so what can be tested here is tested: the label the page composes and
the contract it keeps with the base class. The screen itself is checked by hand.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from components.templates.standard_page import StandardPage
from pages.collection.collections_page import CollectionsPage


class TestPageContract:
    """The page is a `StandardPage` with one, two or three cards per row."""

    def test_it_is_a_standard_page(self) -> None:
        assert issubclass(CollectionsPage, StandardPage)

    def test_the_grid_is_three_columns_on_a_wide_window(self) -> None:
        assert CollectionsPage.GRID_COLUMNS == {"sm": 12, "md": 6, "lg": 4}


class TestCountLabel:
    """The counter comes from the locale key, never from a literal."""

    def test_it_passes_the_count_to_the_key(self, mocker) -> None:
        mocker.patch(
            "pages.collection.collections_page._",
            side_effect=lambda key, **values: f"{key}:{values['count']}",
        )

        assert CollectionsPage.count_label(3) == "collections.count:3"


class PageTest:
    """A page built on a mocked `ft.Page`, which is enough to inspect it."""

    @pytest.fixture
    def page(self) -> MagicMock:
        page = MagicMock(spec=ft.Page)
        page.route = "/collections"
        page.overlay = []
        page.run_task = MagicMock()
        page.update = MagicMock()
        page.push_route = AsyncMock()
        return page

    @pytest.fixture
    def view(self, page) -> CollectionsPage:
        return CollectionsPage(page, service=MagicMock())

    @staticmethod
    def row(name: str = "Isabel II") -> dict:
        return {
            "id": 1,
            "name": name,
            "series": 3,
            "stamps": 9,
            "total": 14,
            "covers": [{"year": 1850, "code": "C0"}],
        }


class TestConstruction(PageTest):
    """The page builds with the header, the drawer and the four blocks."""

    def test_it_builds(self, view):
        assert view.content_area is not None
        assert view.drawer is not None

    def test_the_header_has_no_separator(self, view):
        """The revised mockup has no user on the right, so nothing to separate."""
        assert len(view.header.left_area.controls) == 2
        assert view.header.right_area.controls == []


class TestRender(PageTest):
    """The grid, the counter and the empty state follow the data."""

    def test_it_paints_one_card_per_collection(self, view, mocker):
        mocker.patch(
            "pages.collection.collections_page._",
            side_effect=lambda key, **values: key,
        )
        view._collections = [self.row("A"), self.row("B")]

        with patch(
            "components.collection.collection_card.os.path.exists", return_value=True
        ):
            view._render()

        assert len(view._grid.controls) == 2
        assert all(
            card.col == CollectionsPage.GRID_COLUMNS for card in view._grid.controls
        )
        assert view._grid.visible is True
        assert view._empty.visible is False

    def test_an_empty_list_shows_the_empty_state(self, view, mocker):
        mocker.patch(
            "pages.collection.collections_page._",
            side_effect=lambda key, **values: key,
        )
        view._collections = []

        view._render()

        assert view._grid.visible is False
        assert view._empty.visible is True
        assert view._grid.controls == []


class TestOpenCollection(PageTest):
    """A card is a door to the collection's series (B3)."""

    def test_the_cards_receive_the_open_handler(self, view, mocker):
        mocker.patch(
            "pages.collection.collections_page._",
            side_effect=lambda key, **values: key,
        )
        view._collections = [self.row()]

        with patch(
            "components.collection.collection_card.os.path.exists", return_value=True
        ):
            view._render()

        assert view._grid.controls[0].on_click is not None

    async def test_it_pushes_the_collection_route(self, view, page):
        await view._push_collection(5)

        page.push_route.assert_awaited_once_with("/collections/5")
