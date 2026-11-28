"""Tests for the collection series screen (plan step B3).

`ft.View` cannot be built in this suite, so the page is built on a mocked `ft.Page`,
which is enough for the constructor, the header label and the render. The wiring with
the API is checked through the service tests and by hand.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from components.buttons.primary_button import PrimaryButton
from components.constants import PAGE_SCROLL_GUTTER
from core.collection_names import CollectionNames
from components.form.dropdown import Dropdown as HouseDropdown
from core.translations import _
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

    def test_the_header_carries_the_menu_and_the_path(self, view):
        assert len(view.header.left_area.controls) == 1
        assert view.header.center_area.controls == [view._crumbs]

    def test_the_content_scrolls_in_a_list_with_a_gutter(self, view):
        """A list, not a column: its right padding is where the scrollbar floats."""
        content = view.content_area.content

        assert isinstance(content, ft.ListView)
        assert content.padding == ft.Padding.only(right=PAGE_SCROLL_GUTTER)

    def test_the_paginator_offers_15_30_and_50(self, view):
        assert [option.key for option in view._pagination._dropdown.options] == [
            "15",
            "30",
            "50",
        ]


class TestFilters(PageTest):
    """The filters are the mockup's card, with the controls of the rest of the app."""

    def test_the_row_inside_the_card_does_not_wrap(self, view):
        """A wrapping Row with an expand child breaks Flutter (B5)."""
        card = view._build_filters()

        assert card.content.wrap is not True

    def test_the_card_carries_the_four_filters_and_the_add_action(self, view):
        card = view._build_filters()
        controls = card.content.controls

        assert controls[:4] == [
            view._name_field,
            view._from_year,
            view._to_year,
            view._sort,
        ]
        assert isinstance(controls[-1], PrimaryButton)
        assert controls[-1].on_click == view._open_add_dialog

    def test_the_two_year_boxes_are_numbers(self, view):
        assert view._from_year.keyboard_type == ft.KeyboardType.NUMBER
        assert view._to_year.keyboard_type == ft.KeyboardType.NUMBER

    def test_the_sort_wears_the_house_dropdown(self, view):
        """The same underline and label as the fields beside it, not `ft.Dropdown`."""
        assert isinstance(view._sort, HouseDropdown)


class TestYearFilter(PageTest):
    """The two boxes become the endpoint's `year` parameter."""

    def test_both_bounds_are_a_range(self):
        assert CollectionSeriesPage.year_filter("1850", "1860") == "1850-1860"

    def test_one_bound_leaves_the_other_end_open(self):
        assert CollectionSeriesPage.year_filter("1850", "") == "1850-"
        assert CollectionSeriesPage.year_filter("", "1860") == "-1860"

    def test_nothing_typed_asks_for_nothing(self):
        assert CollectionSeriesPage.year_filter("", None) == ""

    def test_half_typed_or_junk_is_ignored(self):
        assert CollectionSeriesPage.year_filter("18a", "") == ""
        assert CollectionSeriesPage.year_filter("1850", "x") == "1850-"


class TestCrumbs(PageTest):
    """The path lives in the header, not in a row of the page (plan D1)."""

    def test_the_header_carries_it_in_the_middle(self, view):
        """The middle is the space that stretches, so the names can truncate."""
        assert view.header.center_area.controls == [view._crumbs]

    def test_a_remembered_name_is_there_from_the_start(self, page):
        """Coming back from a series does not paint the header empty first."""
        CollectionNames.remember(7, "Test")

        view = CollectionSeriesPage(
            page, 7, collection_service=MagicMock(), item_service=MagicMock()
        )

        assert view._crumbs.text(1) == "Test"

    def test_the_collection_fills_the_last_step(self, view):
        view._crumbs.set_text(1, "Isabel II")

        assert view._crumbs.text(1) == "Isabel II"

    def test_the_current_step_is_white_and_bold(self, view):
        label = view._crumbs._steps[1]

        assert label.weight == ft.FontWeight.BOLD
        assert label.color == ft.Colors.WHITE


class TestEmptyState(PageTest):
    """An empty collection offers the only door there is."""

    def test_it_carries_the_action_that_adds_the_first_stamp(self, view):
        assert view._empty_action.on_click == view._open_add_dialog
        assert view._empty_action in view._empty_box.controls

    def test_an_empty_page_shows_it(self, view, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: key,
        )
        view._pagination.update_state = MagicMock()

        view._render([])

        assert view._empty_box.visible is True
        assert view._rows_box.visible is False


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

    def test_it_says_what_the_copies_cost(self, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values.get('paid') or values.get('stamps')}"
            ),
        )

        label = CollectionSeriesPage.summary_label(
            {"series": 3, "stamps": 9, "paid": "1240.00"}
        )

        assert label.startswith("collections.summary:9 · ")
        assert "1,240.00" in label

    def test_a_collection_without_prices_leaves_the_part_out(self, mocker):
        mocker.patch(
            "pages.collection.collection_series_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values['series']}/{values['stamps']}"
            ),
        )

        label = CollectionSeriesPage.summary_label(
            {"series": 1, "stamps": 2, "paid": None}
        )

        assert "summary_paid" not in label

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
        assert view._rows_column.controls[0]._open_area.on_click is not None
        assert view._rows_column.controls[0]._remove_icon is not None

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
        assert view._crumbs.text(1) == "Isabel II"
        assert CollectionNames.get(7) == "Isabel II"
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
