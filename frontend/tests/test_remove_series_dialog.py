"""Tests for the dialog that takes a series out of a collection (plan D3).

The service and the page are mocked: what is checked is what the dialog asks, what it
writes and what it reports, and that a refusal leaves the question open.
"""

from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from components.collection.remove_series_dialog import RemoveSeriesDialog


class Dialog:
    """The dialog these tests drive."""

    @staticmethod
    def page() -> MagicMock:
        """A page with an overlay and no rendering."""
        page = MagicMock(spec=ft.Page)
        page.overlay = []
        page.update = MagicMock()
        return page

    @classmethod
    def build(cls, **callbacks) -> RemoveSeriesDialog:
        """A dialog over collection 7, series 3, with five copies."""
        service = MagicMock()
        service.remove_issue = AsyncMock(return_value=MagicMock(status_code=200))
        dialog = RemoveSeriesDialog(
            cls.page(),
            service,
            7,
            3,
            name="Isabel II",
            count=5,
            **callbacks,
        )
        dialog._service.remove_issue.return_value.json.return_value = {
            "data": {"deleted": 5}
        }
        return dialog


class TestQuestion:
    """One question, with the name and the number of copies that leave."""

    def test_it_opens_on_the_overlay(self):
        dialog = Dialog.build()

        dialog.show()

        assert dialog._dialog.open is True
        assert dialog._dialog in dialog.page.overlay

    def test_it_says_the_name_and_the_count(self):
        dialog = Dialog.build()

        dialog.show()

        texts = " ".join(
            control.value
            for control in dialog._dialog.content.controls
            if isinstance(control, ft.Text)
        )

        assert "Isabel II" in texts
        assert "5" in texts


class TestWrite:
    """The dialog writes and reports; the page decides what to do next."""

    async def test_it_removes_the_series_and_reports_the_count(self):
        removed = MagicMock()
        dialog = Dialog.build(on_removed=removed)
        dialog.show()

        await dialog._confirm(None)

        dialog._service.remove_issue.assert_awaited_once_with(7, 3)
        removed.assert_called_once_with(5)
        assert dialog._dialog.open is False

    async def test_a_forbidden_token_closes_and_reports(self):
        forbidden = MagicMock()
        dialog = Dialog.build(on_forbidden=forbidden)
        dialog._service.remove_issue.return_value = MagicMock(status_code=403)
        dialog.show()

        await dialog._confirm(None)

        forbidden.assert_called_once_with()
        assert dialog._dialog.open is False

    async def test_a_failure_keeps_the_question_open(self):
        removed = MagicMock()
        dialog = Dialog.build(on_removed=removed)
        dialog._service.remove_issue.return_value = None
        dialog.show()

        await dialog._confirm(None)

        assert dialog._error.visible is True
        assert dialog._dialog.open is True
        removed.assert_not_called()
