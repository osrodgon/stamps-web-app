"""Tests for the series detail screen (plan step B4).

`ft.View` cannot be built in the suite, so the page is built on a mocked `ft.Page`.
What is checked here is the constructor, the summary label, the render of the series
and the mapping of the write answers; the rest is checked by hand.
"""

from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from components.constants import PAGE_SCROLL_GUTTER
from core.translations import _
from pages.collection.collection_issue_page import CollectionIssuePage


class Details:
    """The detail payload the endpoint returns."""

    @staticmethod
    def issue() -> dict:
        return {
            "id": 3,
            "year": "1850",
            "date": "1850-01-01",
            "name": "Isabel II",
            "country": "España",
            "stamp_type": "Sello",
            "print_type": "Litografía",
            "printer": "Fábrica Nacional",
            "artist": "Bartolomé Coromina",
            "paper_type": "Estucado",
            "perforation": "Sin dentar",
            "total_printed": 5000000,
            "market_value_mnh": "37500.00",
            "market_value_used": "2250.00",
            "description": "…",
            "note": None,
        }

    @staticmethod
    def stamp(with_item: bool) -> dict:
        return {
            "id": 10 if with_item else 11,
            "name": "6 cuartos",
            "edifil_code": "1",
            "fesofi_code": "0001" if with_item else "0002",
            "face_value": "6 cuartos",
            "colors": ["Negro"],
            "market_value_mnh": "300.00",
            "market_value_used": "30.00",
            "item": {
                "id": 4,
                "condition_type": {"id": 1, "name": "Mint"},
                "location": {"id": 2, "name": "Album 1"},
                "quantity": 2,
                "price_paid": "120.00",
                "acquisition_date": "2024-03-12",
                "note": None,
            }
            if with_item
            else None,
        }

    @classmethod
    def payload(cls, neighbours: dict = None) -> dict:
        return {
            "issue": cls.issue(),
            "stamps": [cls.stamp(True), cls.stamp(False)],
            "summary": {"owned": 1, "total": 2, "paid": "120.00"},
            "neighbours": neighbours,
        }


class PageTest:
    """A page built on a mocked `ft.Page`."""

    @pytest.fixture
    def page(self) -> MagicMock:
        page = MagicMock(spec=ft.Page)
        page.route = "/collections/7/issues/3"
        page.overlay = []
        page.run_task = MagicMock()
        page.update = MagicMock()
        page.push_route = AsyncMock()
        return page

    @pytest.fixture
    def view(self, page) -> CollectionIssuePage:
        return CollectionIssuePage(
            page,
            7,
            3,
            collection_service=MagicMock(),
            item_service=MagicMock(),
        )


class TestConstruction(PageTest):
    """The page builds for the pair of ids."""

    def test_it_builds_for_the_series(self, view):
        assert view._collection_id == 7
        assert view._issue_id == 3

    def test_the_content_scrolls_in_a_list_with_a_gutter(self, view):
        """A list, not a column: its right padding is where the scrollbar floats."""
        content = view.content_area.content

        assert isinstance(content, ft.ListView)
        assert content.padding == ft.Padding.only(right=PAGE_SCROLL_GUTTER)

    def test_the_header_has_no_separator(self, view):
        assert len(view.header.left_area.controls) == 2
        assert view.header.right_area.controls == []


class TestSummary(PageTest):
    """`3 of 5 stamps · Paid €315.00`, from the locale keys."""

    def test_it_passes_the_three_figures(self, mocker):
        mocker.patch(
            "pages.collection.collection_issue_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values.get('owned')}/{values.get('total')}"
            ),
        )

        label = CollectionIssuePage.summary_label(1, 2, "120.00", "en")

        assert label.startswith("collections.progress:1/2")
        assert "120.00" in label


class TestRender(PageTest):
    """The read-only series and one card per stamp."""

    def test_it_paints_the_series_and_its_stamps(self, view, mocker):
        mocker.patch(
            "pages.collection.collection_issue_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values.get('owned')}/{values.get('total')}"
            ),
        )

        view._render(Details.payload())

        assert len(view._cards) == 2
        assert view._cards[0].item is not None
        assert view._cards[1].item is None
        assert view._detail_box.visible is True
        assert view._series_crumb.value == "Isabel II"

    def test_the_summary_follows_the_cards(self, view, mocker):
        mocker.patch(
            "pages.collection.collection_issue_page._",
            side_effect=lambda key, **values: (
                f"{key}:{values.get('owned')}/{values.get('total')}"
            ),
        )
        view._render(Details.payload())

        view._cards[0].set_item(None)

        assert view._summary_text.value.startswith("collections.progress:0/2")


class TestLayout(PageTest):
    """The stamps section of the mockup: a head and two cards per row."""

    def test_the_head_does_not_align_by_baseline(self, view):
        """`BASELINE` needs a `textBaseline` Flet does not send and collapses the page."""
        head = view._stamps_head()

        assert head.content.vertical_alignment is not ft.CrossAxisAlignment.BASELINE
        assert head.content.controls[0].value == _("collections.stamps_section")

    def test_the_cards_are_a_two_column_grid(self, view):
        view._render(Details.payload())

        cards = view._cards_row

        assert isinstance(cards, ft.ResponsiveRow)
        assert len(cards.controls) == 2
        assert all(
            card.col[ft.ResponsiveRowBreakpoint.LG] == 6 for card in cards.controls
        )


class TestNeighbours(PageTest):
    """The arrows walk the collection's list, in its order."""

    def test_the_position_and_both_arrows(self, view):
        view._render(
            Details.payload(
                {"position": 2, "total": 5, "previous": 1, "next": 3}
            )
        )

        assert view._position_text.value == "2 / 5"
        assert view._previous_button.disabled is False
        assert view._next_button.disabled is False

    def test_the_first_series_has_no_previous(self, view):
        view._render(
            Details.payload(
                {"position": 1, "total": 5, "previous": None, "next": 2}
            )
        )

        assert view._previous_button.disabled is True
        assert view._next_button.disabled is False

    def test_without_neighbours_the_arrows_are_hidden(self, view):
        """The catalogue reader has no list behind it."""
        view._render(Details.payload())

        assert view._previous_button.visible is False
        assert view._next_button.visible is False

    def test_an_arrow_opens_the_neighbour(self, view, page):
        view._render(
            Details.payload(
                {"position": 2, "total": 5, "previous": 1, "next": 3}
            )
        )

        view._go_next(None)

        assert page.run_task.called
        assert page.run_task.call_args.args[0].__name__.endswith("__push_series")
        assert page.run_task.call_args.args[1] == 3


class TestRemoveSeries(PageTest):
    """The bin beside the badge takes the series out of the collection."""

    def test_the_bin_is_in_the_badge_row(self, view):
        icons = [
            control
            for control in self.walk(view._build_badge_row())
            if isinstance(control, ft.IconButton)
        ]

        assert icons
        assert icons[0].tooltip == _("collections.remove_series")

    async def test_it_removes_and_goes_back_to_the_list(self, view, page):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": {"deleted": 3}}
        view._item_service.remove_issue = AsyncMock(return_value=response)
        view.show_notification = AsyncMock()
        view._close_dialog = MagicMock()

        await view._remove_series(None)

        view._item_service.remove_issue.assert_awaited_once_with(7, 3)
        page.push_route.assert_awaited_once_with("/collections/7")

    async def test_a_refusal_stays_and_says_so(self, view, page):
        view._item_service.remove_issue = AsyncMock(return_value=None)
        view.show_notification = AsyncMock()
        view._close_dialog = MagicMock()

        await view._remove_series(None)

        page.push_route.assert_not_awaited()
        view.show_notification.assert_awaited()

    @staticmethod
    def walk(control) -> list:
        """Every control of the tree."""
        found: list = [control]
        for child in (getattr(control, "controls", None) or []):
            found.extend(TestRemoveSeries.walk(child))
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, int, float)):
            found.extend(TestRemoveSeries.walk(content))
        return found


class TestWrites(PageTest):
    """The page maps the API's answers without inventing anything."""

    async def test_a_save_returns_the_item(self, view):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": {"id": 4, "quantity": 3}}
        view._item_service.update_item = AsyncMock(return_value=response)

        saved = await view._save_item({}, 4, {"quantity": 3})

        assert saved == {"id": 4, "quantity": 3}

    async def test_an_add_returns_the_new_item(self, view):
        response = MagicMock()
        response.status_code = 201
        response.json.return_value = {"data": {"id": 5}}
        view._item_service.add_item = AsyncMock(return_value=response)

        added = await view._add_item({"id": 11})

        assert added == {"id": 5}

    async def test_a_duplicate_reloads_the_detail(self, view):
        response = MagicMock()
        response.status_code = 409
        view._item_service.add_item = AsyncMock(return_value=response)
        view._load_detail = AsyncMock()

        added = await view._add_item({"id": 11})

        assert added is None
        view._load_detail.assert_awaited_once_with()

    async def test_a_remove_answers_whether_it_worked(self, view):
        response = MagicMock()
        response.status_code = 200
        view._item_service.delete_item = AsyncMock(return_value=response)

        assert await view._remove_item(4) is True
