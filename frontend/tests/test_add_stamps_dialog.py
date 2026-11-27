"""Tests for the dialog that adds stamps from the catalogue (plan step C4).

The page and the service are mocked: what is checked is what the dialog asks for,
what it writes and what it says afterwards. The lists it paints are walked as
controls, because Flet cannot render in the suite.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from components.buttons.default_button import DefaultButton
from components.form.dialogs.add_stamps_dialog import AddStampsDialog


class Texts:
    """Every visible string of a control tree."""

    @classmethod
    def of(cls, control) -> list[str]:
        """Walk the controls and collect the `Text` values."""
        found: list[str] = []
        if isinstance(control, ft.Text):
            found.append(control.value or "")
            found.extend(span.text for span in (control.spans or []))
        for child in (getattr(control, "controls", None) or []):
            found.extend(cls.of(child))
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, int, float)):
            found.extend(cls.of(content))
        return found

    @classmethod
    def walk(cls, control) -> list:
        """Every control of the tree, the containers included."""
        found: list = [control]
        for child in (getattr(control, "controls", None) or []):
            found.extend(cls.walk(child))
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, int, float)):
            found.extend(cls.walk(content))
        return found


class Answer:
    """The payloads the endpoints return."""

    @staticmethod
    def page(issues: list, has_more: bool = False, total: int = None) -> MagicMock:
        """One page of the catalogue."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "issues": issues,
                "pagination": {
                    "total": total if total is not None else len(issues),
                    "has_more": has_more,
                },
            }
        }
        return response

    @staticmethod
    def detail(stamps: list, year: int = 1852) -> MagicMock:
        """One series with its stamps and the year of the issue."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": {"issue": {"id": 3, "year": year}, "stamps": stamps}
        }
        return response

    @staticmethod
    def added(created: int, skipped: int = 0) -> MagicMock:
        """The answer of a bulk add."""
        response = MagicMock()
        response.status_code = 201
        response.json.return_value = {
            "data": {
                "created": created,
                "skipped": skipped,
                "total": created + skipped,
            }
        }
        return response

    @staticmethod
    def refused(status_code: int = 400, message: str = "Too many.") -> MagicMock:
        """A refusal of the API."""
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = {
            "errors": [{"field": None, "message": message, "code": "other"}]
        }
        return response


class Catalogue:
    """The series and stamps these tests read."""

    @staticmethod
    def issue(
        issue_id: int = 3,
        total: int = 5,
        owned: int = 2,
        year: int = 1852,
    ) -> dict:
        """One row of the catalogue page."""
        return {
            "id": issue_id,
            "year": year,
            "date": f"{year}-02-01",
            "name": "Isabel II",
            "country": "España",
            "stamp_type": "Sello",
            "cover": {"year": year, "code": "0012"},
            "total_stamps": total,
            "owned_stamps": owned,
        }

    @staticmethod
    def stamp(stamp_id: int, owned: bool = False) -> dict:
        """One stamp of a series."""
        return {
            "id": stamp_id,
            "name": "Isabel II",
            "face_value": "6 cuartos",
            "color": ["Rosa"],
            "fesofi_code": f"00{stamp_id}",
            "issue_year": 1852,
            "item": {"id": 9} if owned else None,
        }


class DialogTest:
    """The fixtures every class below shares."""

    @pytest.fixture
    def page(self) -> MagicMock:
        """A page with an overlay and no rendering."""
        page = MagicMock(spec=ft.Page)
        page.overlay = []
        page.update = MagicMock()
        page.run_task = MagicMock()
        return page

    @pytest.fixture
    def service(self) -> MagicMock:
        """A catalogue service whose calls the tests decide."""
        service = MagicMock()
        service.search_issues = AsyncMock(
            return_value=Answer.page([Catalogue.issue()])
        )
        service.get_issue = AsyncMock(
            return_value=Answer.detail([Catalogue.stamp(12, owned=True)])
        )
        service.add_stamps = AsyncMock(return_value=Answer.added(1))
        service.add_issue = AsyncMock(return_value=Answer.added(3))
        service.add_year = AsyncMock(return_value=Answer.added(7, 30))
        return service

    @pytest.fixture
    def on_added(self) -> MagicMock:
        """The callback the page passes to reload."""
        return MagicMock()

    @pytest.fixture
    def on_forbidden(self) -> MagicMock:
        """The callback for an expired token."""
        return MagicMock()

    @pytest.fixture
    def dialog(self, page, service, on_added, on_forbidden) -> AddStampsDialog:
        """The dialog, closed and with nothing loaded yet."""
        return AddStampsDialog(
            page,
            service,
            7,
            collection_name="Test",
            on_added=on_added,
            on_forbidden=on_forbidden,
        )


class TestSearch(DialogTest):
    """The two filters of the screen behind, with the same meaning."""

    async def test_it_asks_for_the_first_page_of_twenty(self, dialog, service):
        await dialog.load()

        service.search_issues.assert_awaited_once_with(
            7,
            page=1,
            page_size=20,
            name="",
            year="",
            sort_by="date",
            order="asc",
        )

    async def test_a_name_and_a_range_travel(self, dialog, service):
        dialog._name_field.value = "Isabel"
        dialog._from_field.value = "1850"
        dialog._to_field.value = "1860"

        await dialog.load()

        call = service.search_issues.call_args
        assert call.kwargs["name"] == "Isabel"
        assert call.kwargs["year"] == "1850-1860"

    async def test_one_year_offers_the_whole_year(self, dialog, service):
        dialog._from_field.value = "1852"
        dialog._to_field.value = "1852"

        await dialog.load()

        assert dialog._year == 1852
        assert dialog._year_button.visible is True
        assert "1852" in dialog._year_button.content.value

    async def test_the_list_keeps_its_page_and_the_year_is_counted_apart(
        self, dialog, service
    ):
        """The page of twenty cannot answer how many stamps a year has."""
        dialog._from_field.value = "1852"
        dialog._to_field.value = "1852"

        await dialog.load()

        calls = service.search_issues.await_args_list

        assert calls[0].kwargs["page_size"] == 20
        assert calls[1].kwargs["page_size"] == 0
        assert calls[1].kwargs["year"] == "1852-1852"
        assert calls[1].kwargs["name"] == ""

    async def test_one_box_is_enough_to_name_the_year(self, dialog, service):
        """`From 1852` filters from 1852 on and still offers 1852 whole."""
        dialog._from_field.value = "1852"

        await dialog.load()

        assert dialog._year == 1852
        assert dialog._year_button.visible is True
        assert service.search_issues.await_args_list[0].kwargs["year"] == "1852-"

    async def test_the_rows_say_what_is_held(self, dialog):
        await dialog.load()

        texts = " · ".join(Texts.of(dialog._results))

        assert "Isabel II" in texts
        assert "2 of 5 in this collection" in texts
        assert "Add the missing 3" in texts

    async def test_a_complete_series_is_not_offered_again(self, dialog, service):
        service.search_issues.return_value = Answer.page(
            [Catalogue.issue(total=5, owned=5)]
        )

        await dialog.load()

        assert "Already complete" in " · ".join(Texts.of(dialog._results))

    async def test_an_empty_search_says_so(self, dialog, service):
        service.search_issues.return_value = Answer.page([])

        await dialog.load()

        assert dialog._empty.visible is True


class TestYearFilter(DialogTest):
    """The two boxes become the endpoint's `year`, as the screen behind does."""

    def test_a_range_needs_both_ends(self):
        assert AddStampsDialog.year_filter("1850", "1860") == "1850-1860"
        assert AddStampsDialog.year_filter("1850", "") == "1850-"
        assert AddStampsDialog.year_filter("", "1860") == "-1860"
        assert AddStampsDialog.year_filter("", "") == ""

    def test_one_year_is_named_by_one_box(self):
        assert AddStampsDialog.year_of("1852", "1852") == 1852
        assert AddStampsDialog.year_of("1852", "") == 1852
        assert AddStampsDialog.year_of("", "1853") == 1853
        assert AddStampsDialog.year_of("1852", "1853") is None
        assert AddStampsDialog.year_of("", "") is None


class TestUnfold(DialogTest):
    """Unfolding reads the series once and marks the copies already there."""

    async def test_it_reads_the_series_and_paints_its_stamps(
        self, dialog, service
    ):
        await dialog.load()

        await dialog._toggle(dialog._issues[0])

        service.get_issue.assert_awaited_once_with(7, 3)
        texts = " · ".join(Texts.of(dialog._results))
        assert "In this collection" in texts

    async def test_the_year_of_the_issue_reaches_every_stamp(self, dialog):
        """The picture is `<year>/<code>`, and the stamp payload has no year."""
        await dialog.load()

        await dialog._toggle(dialog._issues[0])

        stamps = dialog._issues[0]["detail"]["stamps"]
        assert [stamp["issue_year"] for stamp in stamps] == [1852]

    async def test_unfolding_twice_closes_without_another_call(
        self, dialog, service
    ):
        await dialog.load()
        await dialog._toggle(dialog._issues[0])

        await dialog._toggle(dialog._issues[0])

        assert service.get_issue.await_count == 1
        assert dialog._issues[0]["detail"] is None

    def test_no_row_wraps_with_an_expand_child(self, dialog):
        """The B5 trap: a wrapping Row with an expand child collapses the page."""
        rows = [control for control in dialog._results.controls]

        def wraps(control) -> bool:
            if isinstance(control, ft.Row) and control.wrap is True:
                return True
            for child in (getattr(control, "controls", None) or []):
                if wraps(child):
                    return True
            content = getattr(control, "content", None)
            if content is not None and not isinstance(content, (str, int)):
                return wraps(content)
            return False

        assert not any(wraps(row) for row in rows)


class TestHandlersAreScheduled(DialogTest):
    """Flet drops a coroutine returned by a sync handler: these schedule it.

    The first build wired the row's buttons to `lambda event: self._add_issue(...)`,
    which returned a coroutine nobody awaited — the buttons did nothing at all.
    """

    async def test_the_row_action_schedules_the_write(self, dialog, page):
        await dialog.load()

        button = [
            control
            for control in Texts.walk(dialog._results)
            if isinstance(control, DefaultButton)
            and control.content.value == "Add the missing 3"
        ][0]

        button.on_click(None)

        assert page.run_task.called
        assert page.run_task.call_args.args[0] == dialog._add_issue

    async def test_the_chevron_schedules_the_read(self, dialog, page):
        await dialog.load()

        chevron = [
            control
            for control in Texts.walk(dialog._results)
            if isinstance(control, ft.IconButton)
        ][0]

        chevron.on_click(None)

        assert page.run_task.call_args.args[0] == dialog._toggle


class TestWrites(DialogTest):
    """One stamp, one series or one year: one request each."""

    async def test_adding_a_stamp(self, dialog, service, on_added):
        await dialog._add_stamp(Catalogue.stamp(12))

        service.add_stamps.assert_awaited_once_with(7, [12])
        on_added.assert_called_once_with(1, 0)

    async def test_adding_a_series_small_enough_writes_at_once(
        self, dialog, service, on_added
    ):
        await dialog.load()

        await dialog._add_issue(dialog._issues[0], 3)

        service.add_issue.assert_awaited_once_with(7, 3)
        on_added.assert_called_once_with(3, 0)

    async def test_a_big_series_asks_first(self, dialog, service):
        await dialog.load()

        await dialog._add_issue(dialog._issues[0], 37)

        service.add_issue.assert_not_awaited()
        assert dialog._confirm is not None
        assert dialog._confirm.open is True

        await dialog._confirm_and_write(
            lambda: dialog._AddStampsDialog__write_issue(dialog._issues[0])
        )

        service.add_issue.assert_awaited_once_with(7, 3)

    async def test_adding_a_year(self, dialog, service, on_added):
        dialog._from_field.value = "1852"
        dialog._to_field.value = "1852"
        await dialog.load()

        await dialog._add_year(None)

        service.add_year.assert_awaited_once_with(7, 1852)
        on_added.assert_called_once_with(7, 30)

    async def test_the_counts_are_said_in_the_footer(self, dialog):
        dialog._from_field.value = "1852"
        dialog._to_field.value = "1852"
        await dialog.load()

        await dialog._add_year(None)

        assert dialog._status.value == "7 added · 30 already there"

    async def test_a_refusal_is_shown_and_nothing_reloads(
        self, dialog, service, on_added
    ):
        service.add_issue.return_value = Answer.refused(400, "501 stamps asked for.")

        await dialog.load()
        await dialog._add_issue(dialog._issues[0], 3)

        assert dialog._error.visible is True
        assert "501" in dialog._error.value
        on_added.assert_not_called()

    async def test_a_forbidden_token_closes_and_reports(
        self, dialog, service, on_forbidden
    ):
        service.add_issue.return_value = Answer.refused(403)

        await dialog.load()
        await dialog._add_issue(dialog._issues[0], 3)

        on_forbidden.assert_called_once_with()
