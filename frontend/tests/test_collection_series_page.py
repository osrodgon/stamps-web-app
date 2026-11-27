"""Tests for the collection series screen (plan step B3).

`ft.View` cannot be built in this suite, so the page is built on a mocked `ft.Page`,
which is enough for the constructor, the header label and the render. The wiring with
the API is checked through the service tests and by hand.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from pages.collection.collection_series_page import CollectionSeriesPage


class PageTest:
    """A page built on a mocked `ft.Page`."""

    @pytest.fixture
    def page(self) -> MagicMock:
        page = MagicMock(spec=ft.Page)
        page.route = "/collections/7"
        page.overlay = []
        page.run_task = MagicMock()
        page.update = MagicMock()
        page.push_route = AsyncMock()
        return page

    @pytest.fixture
    def view(self, page) -> CollectionSeriesPage:
        return CollectionSeriesPage(
            page,
            7,
            collection_service=MagicMock(),
            item_service=MagicMock(),
            issue_service=MagicMock(),
        )

    @staticmethod
    def row(name: str = "Isabel II") -> dict:
        return {
            "id": 1,
            "year": 1850,
            "date": "1850-01-01",
            "name": name,
            "country": "España",
            "stamp_type": "Sello",
            "cover": None,
            "total_stamps": 5,
            "owned_stamps": 3,
            "paid": "315.00",
            "catalogue_mnh": "24850.00",
        }


class TestConstruction(PageTest):
    """The page builds with the header, the filters and the paginator."""

    def test_it_builds_for_the_collection(self, view):
        assert view._collection_id == 7
        assert view._sort_key == CollectionSeriesPage.DEFAULT_SORT

    def test_the_header_has_no_separator(self, view):
        assert len(view.header.left_area.controls) == 2
        assert view.header.right_area.controls == []

    def test_the_paginator_offers_15_30_and_50(self, view):
        assert [option.key for option in view._pagination._dropdown.options] == [
            "15",
            "30",
            "50",
        ]


class TestFilters(PageTest):
    """The filter row does not wrap: a wrapping Row with an expand child breaks."""

    def test_the_filters_row_does_not_wrap(self, view):
        row = view._build_filters()

        assert row.wrap is not True


class TestSummary(PageTest):
    """The header's counters come from the overview row."""

    def test_it_passes_both_counts_to_the_key(self, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values['series']}/{values['stamps']}"
            ),
        )

        label = CollectionSeriesPage.summary_label({"series": 3, "stamps": 9})

        assert label == "collections.summary:3/9"

    def test_an_empty_collection_reads_zero(self, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: f"{values['series']}/{values['stamps']}",
        )

        assert CollectionSeriesPage.summary_label({}) == "0/0"


class TestRender(PageTest):
    """The rows, the empty state and the paginator follow the data."""

    def test_it_paints_one_row_per_series(self, view):
        view._pagination.update_state = MagicMock()
        view._total = 2

        with patch(
            "components.collection.issue_progress_card.os.path.exists",
            return_value=False,
        ):
            view._render([self.row("A"), self.row("B")])

        assert len(view._rows_column.controls) == 2
        assert view._rows_box.visible is True
        assert view._empty_text.visible is False
        assert view._pagination.visible is True
        assert view._rows_column.controls[0].on_click is not None

    def test_an_empty_page_shows_the_empty_state(self, view, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: key,
        )
        view._pagination.update_state = MagicMock()

        view._render([])

        assert view._rows_box.visible is False
        assert view._empty_text.visible is True
        assert view._empty_text.value == "collections.no_series_yet"
        assert view._pagination.visible is False

    def test_an_empty_filter_result_says_so(self, view, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: key,
        )
        view._pagination.update_state = MagicMock()
        view._name_filter = "nothing"

        view._render([])

        assert view._empty_text.value == "collections.empty_series"


class TestCollectionLoading(PageTest):
    """The header is filled from the overview row, not from a new endpoint."""

    async def test_a_found_collection_fills_the_header(self, view):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": [{"id": 7, "name": "Isabel II", "series": 3, "stamps": 9}]
        }
        view._collection_service.get_collections = AsyncMock(return_value=response)

        await view._load_collection()

        assert view._name_text.value == "Isabel II"
        assert view._crumb_name.value == "Isabel II"
        assert view._collection is not None

    async def test_a_missing_collection_goes_back_to_the_list(self, view):
        view.show_notification = AsyncMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        view._collection_service.get_collections = AsyncMock(return_value=response)

        await view._load_collection()

        view.main_page.push_route.assert_awaited_once_with("/collections")


class TestOpenSeries(PageTest):
    """A row is a door to the series detail (B4)."""

    async def test_it_pushes_the_series_route(self, view, page):
        await view._push_issue(3)

        page.push_route.assert_awaited_once_with("/collections/7/issues/3")
